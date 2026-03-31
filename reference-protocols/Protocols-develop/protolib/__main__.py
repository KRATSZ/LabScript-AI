from protolib import merge
from protolib.traversals import PROTOCOLS_BUILD_DIR

print(PROTOCOLS_BUILD_DIR)
merge.merge_protocols(PROTOCOLS_BUILD_DIR)
