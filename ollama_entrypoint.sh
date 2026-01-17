#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
pid=$!

# Wait for Ollama to actually wake up.
echo "🔴 Waiting for Ollama API..."
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 1
done
echo "🟢 Ollama is ready!"

# Check & Pull 'moondream' (The Eyes)
if ! curl -s http://localhost:11434/api/tags | grep -q "moondream"; then
    echo "⬇️ Pulling moondream model..."
    ollama pull moondream
    echo "✅ moondream installed!"
else
    echo "✅ moondream already exists."
fi

# Check & Pull 'llama3.2:1b' (The Brain)
if ! curl -s http://localhost:11434/api/tags | grep -q "llama3.2:1b"; then
    echo "⬇️ Pulling llama3.2:1b model..."
    ollama pull llama3.2:1b
    echo "✅ llama3.2:1b installed!"
else
    echo "✅ llama3.2:1b already exists."
fi

# Wait for the background process to finish (keeps container alive)
wait $pid