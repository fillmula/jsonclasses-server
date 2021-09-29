def raise_kindly():
    raise ModuleNotFoundError('please install inflection for key convension '
                              'behavior')


def cname_to_pname(cname: str) -> str:
    try:
        from inflection import dasherize, underscore, pluralize
    except ModuleNotFoundError as e:
        raise_kindly()
    return dasherize(pluralize(underscore(cname)))


def fname_to_pname(fname: str) -> str:
    try:
        from inflection import dasherize, underscore
    except ModuleNotFoundError as e:
        raise_kindly()
    return dasherize(underscore(fname))


def pname_to_cname(pname: str) -> str:
    try:
        from inflection import camelize, underscore, singularize
    except ModuleNotFoundError as e:
        raise_kindly()
    return camelize(underscore(singularize(pname)))


def pname_to_fname(pname: str) -> str:
    try:
        from inflection import underscore
    except ModuleNotFoundError as e:
        raise_kindly()
    return underscore(pname)


def cname_to_srname(cname: str) -> str:
    try:
        from inflection import singularize, camelize
    except ModuleNotFoundError as e:
        raise_kindly()
    return singularize(camelize(cname, False))
