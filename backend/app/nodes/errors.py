class NodeError(Exception):
    """节点错误基类"""
    pass

class NodeNotFoundError(NodeError):
    """节点不存在错误"""
    pass

class NodeUnhealthyError(NodeError):
    """节点不健康错误"""
    pass

class NodeOperationError(NodeError):
    """节点操作错误"""
    pass

class NodeResourceError(NodeError):
    """节点资源错误"""
    pass

class NodeStorageError(NodeError):
    """节点存储错误"""
    pass 