import setuptools

setuptools.setup(
    name="review_wof",
    version="0.0.1",
    author="Barak Korren",
    author_email="bkorren@redhat.com",
    description="Code reviewers wall of fame dashboard.",
    long_description=(
        "# Review wall of fame\n\n"
        "Small web application to present code review statistics"
    ),
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
    ],
    install_requires = ["gunicorn", "Flask", "python-dotenv"],
)
