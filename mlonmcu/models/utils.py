import os
import numpy as np
from pathlib import Path


def make_hex_array(filename, mode="bin"):
    out = ""
    if mode == "bin":
        with open(filename, "rb") as f:
            data = f.read(1)
            while data:
                out += "0x" + data.hex() + ", "
                data = f.read(1)
    elif mode == "npy":
        data = np.load(filename)
        # TODO: figure out endianess
        byte_data = data.tobytes()
        out = ", ".join(["0x{:02x}".format(x) for x in byte_data])
    else:
        raise RuntimeError(f"Unsupported mode: {mode}")
    return out


def fill_data_source(in_bufs, out_bufs):
    out = '#include "ml_interface.h"\n'
    out += "#include <stddef.h>\n"
    out += (
        "const int num_data_buffers_in = "
        + str(sum([len(buf) for buf in in_bufs]))
        + ";\n"
    )
    out += (
        "const int num_data_buffers_out = "
        + str(sum([len(buf) for buf in out_bufs]))
        + ";\n"
    )
    for i, buf in enumerate(in_bufs):
        for j in range(len(buf)):
            out += (
                "const unsigned char data_buffer_in_"
                + str(i)
                + "_"
                + str(j)
                + "[] = {"
                + buf[j]
                + "};\n"
            )
    for i, buf in enumerate(out_bufs):
        for j in range(len(buf)):
            out += (
                "const unsigned char data_buffer_out_"
                + str(i)
                + "_"
                + str(j)
                + "[] = {"
                + buf[j]
                + "};\n"
            )

    var_in = "const unsigned char *const data_buffers_in[] = {"
    var_insz = "const size_t data_size_in[] = {"
    for i, buf in enumerate(in_bufs):
        for j in range(len(buf)):
            var_in += "data_buffer_in_" + str(i) + "_" + str(j) + ", "
            var_insz += "sizeof(data_buffer_in_" + str(i) + "_" + str(j) + "), "
    var_out = "const unsigned char *const data_buffers_out[] = {"
    var_outsz = "const size_t data_size_out[] = {"
    for i, buf in enumerate(out_bufs):
        for j in range(len(buf)):
            var_out += "data_buffer_out_" + str(i) + "_" + str(j) + ", "
            var_outsz += "sizeof(data_buffer_out_" + str(i) + "_" + str(j) + "), "
    out += var_in + "};\n" + var_out + "};\n" + var_insz + "};\n" + var_outsz + "};\n"
    return out


def lookup_data_buffers(input_paths, output_paths):
    assert len(input_paths) > 0
    legacy = False
    used_fmt = None
    allowed_fmts = ["bin", "npy"]

    def helper(paths):
        nonlocal used_fmt, legacy
        data = []
        for i, path in enumerate(paths):
            filenames = os.listdir(path)
            for filename in filenames:
                fmt = Path(filename).suffix[1:]
                if used_fmt is None:
                    used_fmt = fmt
                else:
                    assert (
                        used_fmt == fmt
                    ), "Please only use a single format for inout model data (.bin OR .npy)"
                base = Path(filename).stem
                if fmt not in allowed_fmts:
                    continue
                if "_" in base:
                    legacy = True
                    assert len(paths) == 1, "Legacy mode only allows a single path"
                    data_index, tensor_index = list(map(int, base.split("_")))[:2]
                else:
                    data_index, tensor_index = int(base), i
                hex_data = make_hex_array(Path(path) / filename, mode=used_fmt)
                data.append((data_index, tensor_index, hex_data))
        sorted_data = sorted(data, key=lambda x: (x[0], x[1]))
        # TODO: get rid of this dirty workaround
        ret = []
        for a, b, c in sorted_data:
            if a >= len(ret):
                assert b == 0
                ret.append([c])
            else:
                ret[a].append(c)
        return ret
        # return [d[-1] for d in sorted_data]  # Extract last column

    ins = helper(input_paths)
    outs = helper(output_paths)
    assert len(ins) == len(outs)
    return ins, outs


def get_data_source(input_paths, output_paths):
    assert len(input_paths) == len(output_paths)
    if len(input_paths) == 0:
        return fill_data_source([], [])
    in_bufs, out_bufs = lookup_data_buffers(input_paths, output_paths)
    return fill_data_source(in_bufs, out_bufs)
