import pkg_resources

def is_extra_installed(module):
    # Get a list of all installed distributions
    installed_distributions = pkg_resources.working_set

    # Check if Pydantic is present in the list of installed distributions
    for dist in installed_distributions:
        if dist.project_name.lower() == module:
            return True

    return False