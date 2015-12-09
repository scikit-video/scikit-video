from .xmltodict import parse as xmltodictparser

# python2 only
binary_type = str


def read_n_bytes(f, N):
    """ read_n_bytes(file, n)
    
    Read n bytes from the given file, or less if the file has less
    bytes. Returns zero bytes if the file is closed.
    """
    bb = binary_type()
    while len(bb) < N:
        extra_bytes = f.read(N-len(bb))
        if not extra_bytes:
            break
        bb += extra_bytes
    return bb

def check_dict(dic, key, valueifnot):
    if key not in dic:
        dic[key] = valueifnot
