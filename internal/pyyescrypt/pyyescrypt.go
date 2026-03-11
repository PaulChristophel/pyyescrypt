package pyyescrypt

import (
	"crypto/rand"
	"errors"

	yescrypt "github.com/openwall/yescrypt-go"
)

const saltLength = 16

// GenerateHash returns a modular-crypt yescrypt hash string for the provided
// password.
func GenerateHash(password string) (string, error) {
	salt, err := generateSaltCryptoRand(saltLength)
	if err != nil {
		return "", err
	}
	setting := "$y$j9T$" + salt

	h, err := yescrypt.Hash([]byte(password), []byte(setting))
	if err != nil {
		return "", err
	}
	return string(h), nil
}

// VerifyHash reports whether the provided password matches the stored hash.
func VerifyHash(password, stored string) (bool, error) {
	if stored == "" {
		return false, errors.New("hash string is empty")
	}

	nh, err := yescrypt.Hash([]byte(password), []byte(stored))
	if err != nil {
		return false, err
	}
	return string(nh) == stored, nil
}

func generateSaltCryptoRand(length int) (string, error) {
	const b64Chars = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
	buf := make([]byte, length)
	if _, err := rand.Read(buf); err != nil {
		return "", err
	}
	out := make([]byte, length)
	for i := range length {
		out[i] = b64Chars[int(buf[i])%len(b64Chars)]
	}
	return string(out), nil
}
