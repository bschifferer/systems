#
# Copyright (c) 2022, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import numpy as np

from merlin.core.protocols import Transformable
from merlin.dag import ColumnSelector, Node
from merlin.schema import ColumnSchema, Schema
from merlin.systems.dag.ops.operator import InferenceOperator


class FilterCandidates(InferenceOperator):
    """
    This operator takes the input column and filters out elements of that column
    based on the supplied criteria.
    """

    def __init__(self, filter_out: str, input_col: str = None) -> "FilterCandidates":
        """_summary_

        Parameters
        ----------
        filter_out : str
            the name of the column to use to filter out
        input_col : str, optional
            The target column to filter on, by default None

        Returns
        -------
        FilterCandidates
            A class object is instantiated with param values passed.
        """
        self.filter_out = Node.construct_from(filter_out)
        self._input_col = input_col
        self._filter_out_col = filter_out
        super().__init__()

    @property
    def dependencies(self):
        return self.filter_out

    def compute_input_schema(
        self,
        root_schema: Schema,
        parents_schema: Schema,
        deps_schema: Schema,
        selector: ColumnSelector,
    ) -> Schema:
        """
        Compute the input schema of this node given the root, parents, and dependencies schemas of
        all ancestor nodes.

        Parameters
        ----------
        root_schema : Schema
            The schema representing the input columns to the graph
        parents_schema : Schema
            A schema representing all the output columns of the ancestors of this node.
        deps_schema : Schema
            A schema representing the dependencies of this node.
        selector : ColumnSelector
            A column selector representing a target subset of columns necessary for this node's
            operator

        Returns
        -------
        Schema
            A schema that has the correct representation of all the incoming columns necessary for
            this node's operator to complete its transform.

        Raises
        ------
        ValueError
            Cannot receive more than one input for this node
        """
        input_schema = super().compute_input_schema(
            root_schema, parents_schema, deps_schema, selector
        )

        self._input_col = parents_schema.column_names[0]
        self._filter_out_col = deps_schema.column_names[0]

        return input_schema

    def compute_output_schema(
        self, input_schema: Schema, col_selector: ColumnSelector, prev_output_schema: Schema = None
    ) -> Schema:
        """
        Compute the input schema of this node given the root, parents and dependencies schemas of
        all ancestor nodes.

        Parameters
        ----------
        input_schema : Schema
            The schema representing the input columns to the graph
        col_selector : ColumnSelector
            A column selector representing a target subset of columns necessary for this node's
            operator
        prev_output_schema : Schema
            A schema representing the output of the previous node.

        Returns
        -------
        Schema
            A schema object representing all outputs of this node.
        """
        return Schema([ColumnSchema("filtered_ids", dtype=np.int32)])

    def validate_schemas(
        self, parents_schema, deps_schema, input_schema, output_schema, strict_dtypes=False
    ):
        if len(parents_schema.column_schemas) > 1:
            raise ValueError(
                "More than one input has been detected for this node,"
                / f"inputs received: {input_schema.column_names}"
            )
        if len(deps_schema.column_schemas) > 1:
            raise ValueError(
                "More than one dependency input has been detected"
                / f"for this node, inputs received: {input_schema.column_names}"
            )

        # 1 for deps and 1 for parents
        if len(input_schema.column_schemas) > 2:
            raise ValueError(
                "More than one input has been detected for this node,"
                / f"inputs received: {input_schema.column_names}"
            )

    def transform(
        self, col_selector: ColumnSelector, transformable: Transformable
    ) -> Transformable:
        """
        Transform input dataframe to output dataframe using function logic.

        Parameters
        ----------
        df : TensorTable
            Input tensor dictionary, data that will be manipulated

        Returns
        -------
        TensorTable
            Transformed tensor dictionary
        """
        candidate_ids = transformable[self._input_col]
        filter_ids = transformable[self._filter_out_col]

        filtered_results = candidate_ids.values[~np.isin(candidate_ids.values, filter_ids.values)]
        return type(transformable)({"filtered_ids": filtered_results})
