"""review_wof.py - Build report of patches and reviews
"""
from flask import Flask, render_template

from .model import patch_reviewers_view, patch_summary_view, patches_view
from .model.gerrit_patches import GerritPatches

application = Flask(__name__)


@application.route('/')
def index():
    patches = GerritPatches()
    return render_template(
        'index.html.j2',
        patches_list=patches.views.list.df,
        patch_summary=patches.views.summary.df,
        reviewers_n_patches=patches.views.reviewers.df
    )
