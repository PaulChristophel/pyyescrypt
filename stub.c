#include <Python.h>

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "_stub",
    NULL,
    -1,
    NULL,
};

PyMODINIT_FUNC PyInit__stub(void) {
    return PyModule_Create(&moduledef);
}