package main

import (
	"flag"
	"fmt"
	"io"
	"os"

	pyyescrypt "github.com/PaulChristophel/pyyescrypt/internal/pyyescrypt"
)

func main() {
	if len(os.Args) < 2 {
		usage()
	}
	switch os.Args[1] {
	case "generate":
		runGenerate()
	case "verify":
		runVerify(os.Args[2:])
	default:
		usage()
	}
}

func usage() {
	fmt.Fprintf(os.Stderr, "usage: %s <generate|verify> [flags]\n", os.Args[0])
	os.Exit(2)
}

func readPasswordFromStdin() (string, error) {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

func runGenerate() {
	pw, err := readPasswordFromStdin()
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyyescrypt-cli: %v\n", err)
		os.Exit(1)
	}

	hash, err := pyyescrypt.GenerateHash(pw)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyyescrypt-cli: %v\n", err)
		os.Exit(1)
	}
	fmt.Println(hash)
}

func runVerify(args []string) {
	fs := flag.NewFlagSet("verify", flag.ExitOnError)
	hash := fs.String("hash", "", "stored yescrypt hash")
	_ = fs.Parse(args)
	if *hash == "" {
		fmt.Fprintln(os.Stderr, "pyyescrypt-cli: --hash is required")
		os.Exit(2)
	}

	pw, err := readPasswordFromStdin()
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyyescrypt-cli: %v\n", err)
		os.Exit(1)
	}

	ok, err := pyyescrypt.VerifyHash(pw, *hash)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pyyescrypt-cli: %v\n", err)
		os.Exit(1)
	}
	if ok {
		fmt.Println("1")
	} else {
		fmt.Println("0")
	}
}
