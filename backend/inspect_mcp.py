import importlib, pkgutil, sys
try:
    import mcp
    print('mcp:', getattr(mcp, '__file__', '<no __file__>'))
    try:
        import mcp.client.session as s
        print('mcp.client.session ok')
    except Exception as e:
        print('mcp.client.session error', repr(e))
    try:
        import mcp.client.websocket as w
        print('mcp.client.websocket ok')
    except Exception as e:
        print('mcp.client.websocket error', repr(e))
    print('mcp package submodules:')
    if hasattr(mcp, '__path__'):
        for finder, name, ispkg in pkgutil.iter_modules(mcp.__path__):
            print('-', name, 'pkg' if ispkg else '')
    else:
        print('no __path__')
except Exception as e:
    print('import mcp failed:', repr(e))
    sys.exit(1)
