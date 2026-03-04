package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"unsafe"

	pyyescrypt "github.com/PaulChristophel/pyyescrypt/internal/pyyescrypt"
)

//export yc_generate_hash
func yc_generate_hash(password *C.char, errOut **C.char) *C.char {
	if errOut != nil {
		*errOut = nil
	}
	if password == nil {
		if errOut != nil {
			*errOut = C.CString("password is null")
		}
		return nil
	}

	hash, err := pyyescrypt.GenerateHash(C.GoString(password))
	if err != nil {
		if errOut != nil {
			*errOut = C.CString(err.Error())
		}
		return nil
	}

	return C.CString(hash)
}

//export yc_verify_hash
func yc_verify_hash(password *C.char, hash *C.char, validOut *C.int, errOut **C.char) C.int {
	if errOut != nil {
		*errOut = nil
	}
	if validOut != nil {
		*validOut = 0
	}
	if password == nil || hash == nil {
		if errOut != nil {
			*errOut = C.CString("password or hash is null")
		}
		return 0
	}

	stored := C.GoString(hash)
	ok, err := pyyescrypt.VerifyHash(C.GoString(password), stored)
	if err != nil {
		if errOut != nil {
			*errOut = C.CString(err.Error())
		}
		return 0
	}

	if validOut != nil {
		if ok {
			*validOut = 1
		} else {
			*validOut = 0
		}
	}
	return 1
}

//export yc_free
func yc_free(p unsafe.Pointer) {
	if p != nil {
		C.free(p)
	}
}

func main() {}
