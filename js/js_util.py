import execjs


def exec_js(path, func, *args):
    with open(path, 'r', encoding='UTF-8') as f:
        js_code = f.read()
    context = execjs.compile(js_code)
    try:
        exec_result = context.call(func, *args)
    except Exception as err:
        print(type(err))
        exec_result = err.__getattribute__('doc')
        print(err)
    print(f'javascript {path} {func} execute result = \n{exec_result}')
    return exec_result