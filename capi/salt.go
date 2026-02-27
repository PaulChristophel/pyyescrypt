package main

import "crypto/rand"

func generateSaltCryptoRand(length int) (string, error) {
	const b64Chars = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
	buf := make([]byte, length)
	if _, err := rand.Read(buf); err != nil {
		return "", err
	}
	out := make([]byte, length)
	for i := 0; i < length; i++ {
		out[i] = b64Chars[int(buf[i])%len(b64Chars)]
	}
	return string(out), nil
}
