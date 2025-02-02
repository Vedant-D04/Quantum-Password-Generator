from flask import Flask, render_template, request, jsonify
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler
import time
import random
import string

app = Flask(__name__)

# IBM Quantum account initialization
service = QiskitRuntimeService(
    channel="ibm_quantum",
    token="16a37c9054c5a8516f48ccc8249ffc235eb48f03854c22e62cf16f7f059270c5aeef6e276c6bc33f669a4d376e985d6ab310177e587bed2b2f3e0b379ced3a85"
)

# Restricted special characters
allowed_special_chars = "#_$@!"

def binary_to_password(binary_string, length, include_uppercase, include_numbers, include_symbols):
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_characters = allowed_special_chars  # Only restricted special characters
    
    # Start with the basic set of characters
    charset = lowercase
    if include_uppercase:
        charset += uppercase
    if include_numbers:
        charset += digits
    if include_symbols:
        charset += special_characters
    
    # Ensure the password is of the correct length
    password = ''
    for i in range(length):
        password += random.choice(charset)

    return password

def generate_random_bits(num_bits):
    try:
        max_qubits = 127  # Maximum number of qubits allowed by the backend
        num_qubits = min(num_bits, max_qubits)  # Ensure qubits do not exceed the backend limit

        # Proceed with generating the random bits as before
        qc = QuantumCircuit(num_qubits, num_qubits)
        for qubit in range(num_qubits):
            qc.h(qubit)
        qc.measure(range(num_qubits), range(num_qubits))

        # Transpile the quantum circuit to match the backend's gate set
        backend = service.backends()[1]
        transpiled_qc = transpile(qc, backend)

        job = Sampler(backend).run([transpiled_qc])
        retries = 0
        while retries < 5:
            try:
                result = job.result()
                counts = result[0].data[qc.cregs[0].name].get_counts()
                return counts
            except Exception as e:
                app.logger.error(f"Error in quantum job: {e}")  # Log specific error in quantum job
                retries += 1
                time.sleep(5)
        raise Exception("Failed to generate random bits after multiple retries.")
    
    except Exception as e:
        app.logger.error(f"Error generating random bits: {e}")
        raise e  # Reraise exception to be handled in the generate_password function

def generate_password(length=8, include_uppercase=False, include_numbers=False, include_symbols=False):
    try:
        counts = generate_random_bits(length * 8)
        if not counts:
            return "Error: Quantum backend did not return results."
        
        bit_string = max(counts, key=counts.get)  # Get the most frequent bit string
        
        # Use the quantum randomness to generate a password
        password = binary_to_password(bit_string, length, include_uppercase, include_numbers, include_symbols)
        return password
    except Exception as e:
        print(f"Error generating password: {e}")
        return "Error: Password generation failed."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/password-generator')
def password_generator():
    return render_template('password_generator.html')

@app.route('/generate-password', methods=['POST'])
def generate_password_route():
    try:
        length = int(request.form.get('length', 16))  # Default to 16 if not provided
        if length < 8 or length > 32:
            return jsonify(error="Invalid password length. Must be between 8 and 32."), 400

        options = request.form.getlist('options')

        app.logger.info(f"Received length: {length}, options: {options}")

        include_uppercase = 'uppercase' in options
        include_numbers = 'numbers' in options
        include_symbols = 'symbols' in options

        password = generate_password(length, include_uppercase, include_numbers, include_symbols)
        return jsonify(password=password)

    except Exception as e:
        app.logger.error(f"Error generating password: {e}")
        return jsonify(error="An internal error occurred."), 500

if __name__ == '__main__':
    app.run(debug=True)
