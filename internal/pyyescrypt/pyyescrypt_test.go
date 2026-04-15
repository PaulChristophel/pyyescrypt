package pyyescrypt

import "testing"

func TestZeroBytes(t *testing.T) {
	buf := []byte("secret")

	zeroBytes(buf)

	assertZeroed(t, buf)
}

func TestGenerateHashBytesZeroesPasswordBuffer(t *testing.T) {
	password := []byte("correct horse battery staple")

	hash, err := GenerateHashBytes(password)
	if err != nil {
		t.Fatalf("GenerateHashBytes returned error: %v", err)
	}
	if hash == "" {
		t.Fatal("GenerateHashBytes returned empty hash")
	}

	assertZeroed(t, password)
}

func TestVerifyHashBytesZeroesPasswordBufferOnSuccess(t *testing.T) {
	password := []byte("correct horse battery staple")

	hash, err := GenerateHash("correct horse battery staple")
	if err != nil {
		t.Fatalf("GenerateHash returned error: %v", err)
	}

	ok, err := VerifyHashBytes(password, hash)
	if err != nil {
		t.Fatalf("VerifyHashBytes returned error: %v", err)
	}
	if !ok {
		t.Fatal("VerifyHashBytes returned false for matching password")
	}

	assertZeroed(t, password)
}

func TestVerifyHashBytesZeroesPasswordBufferOnError(t *testing.T) {
	password := []byte("correct horse battery staple")

	ok, err := VerifyHashBytes(password, "")
	if err == nil {
		t.Fatal("VerifyHashBytes returned nil error for empty hash")
	}
	if ok {
		t.Fatal("VerifyHashBytes returned true for empty hash")
	}

	assertZeroed(t, password)
}

func assertZeroed(t *testing.T, buf []byte) {
	t.Helper()

	for i, b := range buf {
		if b != 0 {
			t.Fatalf("buffer not zeroed at index %d: got %d", i, b)
		}
	}
}
