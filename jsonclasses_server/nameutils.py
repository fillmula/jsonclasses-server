from inflection import singularize, camelize, underscore, dasherize, pluralize


def cname_to_pname(cname: str) -> str:
    return dasherize(pluralize(underscore(cname)))


def fname_to_pname(fname: str) -> str:
    return dasherize(underscore(fname))


def pname_to_cname(pname: str) -> str:
    return camelize(underscore(singularize(pname)))


def pname_to_fname(pname: str) -> str:
    return underscore(pname)


def cname_to_srname(cname: str) -> str:
    return singularize(camelize(cname))
