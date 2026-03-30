#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
pid=$!

# Wait for Ollama to actually wake up.
# Uses 'ollama list' instead of curl — curl is not in the ollama/ollama image.
echo "🔴 Waiting for Ollama API..."
while ! /bin/ollama list > /dev/null 2>&1; do
    sleep 1
done
echo "🟢 Ollama is ready!"

# Check & Pull 'moondream' (The Eyes)
if /bin/ollama list | grep -q "moondream"; then
    echo "✅ moondream already exists."
else
    echo "⬇️ Pulling moondream model..."
    /bin/ollama pull moondream
    echo "✅ moondream installed!"
fi

# Check & Pull 'llama3.2:1b' (The Brain)
if /bin/ollama list | grep -q "llama3.2"; then
    echo "✅ llama3.2:1b already exists."
else
    echo "⬇️ Pulling llama3.2:1b model..."
    /bin/ollama pull llama3.2:1b
    echo "✅ llama3.2:1b installed!"
fi

# Wait for the background process to finish (keeps container alive)
wait $pid
