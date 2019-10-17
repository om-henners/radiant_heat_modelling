import setuptools

long_description = 'Placeholder description'


def requirement_filter(candidate):
    """
    Simple filter for requirements.

    Strip comments (lines starting with #) and empty lines. Return the rest.

    :param candidate: line from a requirements.txt file
    :rtype: bool
    """
    candidate = candidate.strip()
    if not candidate.strip():
        return False
    elif candidate.startswith('#'):
        return False
    return True


setuptools.setup(
    name="bushfire_hazard",  # this should match the name of the module
    version="0.0.1",
    author="Henry Walshaw",
    author_email="henry@pythoncharmers.com",
    description="A small example package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(exclude=('tests', 'build',)),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: All rights reserved",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        candidate.strip()
        for candidate in
        filter(requirement_filter, open('requirements.txt'))
    ],  # any additional 3rd party packages that should be installed
)
