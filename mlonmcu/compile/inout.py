import os


def make_hex_array(fileName):
    out = ""
    with open(fileName, "rb") as f:
        data = f.read(1)
        while data:
            out += "0x" + data.hex() + ", "
            data = f.read(1)
    return out


# TODO: split into multiple functions
# TODO: resolve model data before, just process raw bytes here
def write_inout_data(model, destination, skip=False):
    in_bufs = []
    out_bufs = []
    while not skip and model:
        new_bufs = []
        while True:
            in_filename = os.path.join(
                str(model.data.directory),
                "input",
                str(len(in_bufs)) + "_" + str(len(new_bufs)) + ".bin",
            )
            if not os.path.exists(inFileName):
                in_filename = os.path.join(
                    str(model.data.directory), "input", str(len(in_bufs)) + ".bin"
                )
                if os.path.exists(in_filename):
                    new_bufs.append(make_hex_array(in_filename))
                break
            new_bufs.append(make_hex_array(in_filename))
        in_bufs.append(new_bufs)
        if len(new_bufs) == 0:
            break
        new_bufs = []
        while True:
            if not model.data:
                break
            outFileName = os.path.join(
                str(model.data.directory),
                "output",
                str(len(out_bufs)) + "_" + str(len(newBufs)) + ".bin",
            )
            if not os.path.exists(out_fileName):
                outFileName = os.path.join(
                    str(model.data.directory), "output", str(len(out_bufs)) + ".bin"
                )
                if os.path.exists(out_filename):
                    newBufs.append(make_hex_array(outFileName))
                break
            newBufs.append(makeHexArray(outFileName))
        out_bufs.append(newBufs)
        if len(newBufs) == 0:
            raise RuntimeError("Did not find model output for given input")

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
    assert destination is not None
    dataFileName = str(destination)
    with open(dataFileName, "w") as f:
        f.write(out)