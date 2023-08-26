#!/bin/bash

# Check if Rust is installed
if ! command -v rustc &> /dev/null; then
    echo "Rust is not installed. Installing Rust..."
    
    # Install Rust using rustup
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    
    # Set up environment variables
    source $HOME/.cargo/env
    
    echo "Rust has been installed."
else
    echo "Rust is already installed."
fi
