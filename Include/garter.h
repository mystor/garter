#ifndef Py_GARTER_H
#define Py_GARTER_H
#ifdef __cplusplus
extern "C" {
#endif

PyAPI_FUNC(PyObject *) Garter_NewGlobalScope();

PyAPI_FUNC(int) Garter_Validate(mod_ty mod,
                                PyObject *filename,
                                PyObject *global_scope);

#ifdef __cplusplus
}
#endif
#endif /* !Py_GARTER_H */
