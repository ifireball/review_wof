"""model/patch_summary_view.py - DV Showing a summary about patches
"""
from .base import DataFrameView
from .gerrit_patches import GerritPatches
from . import patches_view


@GerritPatches.view('summary')
class PatchSummaryView(DataFrameView):
    def create_dataframe(self, dsc):
        list_df = dsc.views.list.df
        df = list_df.groupby('state').agg({'number': 'count'})
        df.reset_index(inplace=True)
        df.rename(columns={'number': 'count'})
        return df
