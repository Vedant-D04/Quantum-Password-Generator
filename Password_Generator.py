from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler
import time

# Step 1: Load IBM Quantum Account using QiskitRuntimeService with your API token
service = QiskitRuntimeService(channel="ibm_quantum", token="api token"

# Check if the service is loaded successfully
print("IBM Quantum account successfully loaded!")

# Step 2: Define the quantum circuit for generating random bits
def binary_to_password(binary_string, length):
    """
    Convert a binary string to a password.
    Each 8 bits represent one character.
    Replace non-printable characters with a random printable character.
    """
    printable_range = list(range(33, 127))  # ASCII values of printable characters ('!' to '~')
    password = ''
    
    for i in range(0, len(binary_string), 8):  # Split into 8-bit chunks
        byte = binary_string[i:i+8]
        char_code = int(byte, 2)
        
        # If the character is printable, add it; otherwise, map to a printable character
        if 33 <= char_code <= 126:
            password += chr(char_code)
        else:
            # Map non-printable characters to the printable range deterministically
            mapped_char = chr(printable_range[char_code % len(printable_range)])
            password += mapped_char
    
    return password


def generate_random_bits(num_bits):
    """
    Generate random bits using a quantum circuit with Qiskit's RNG.
    """
    num_qubits = num_bits  # One qubit per random bit
    qc = QuantumCircuit(num_qubits, num_qubits)  # Create the quantum circuit with qubits and classical register
    
    # Apply Hadamard gate to each qubit to create superposition
    for qubit in range(num_qubits):
        qc.h(qubit)
    
    # Measure all qubits into the classical register
    qc.measure(range(num_qubits), range(num_qubits))

    # Transpile the quantum circuit to match the backend's gate set
    backend = service.backends()[1]  # Use the second available backend (Kyiv)
    transpiled_qc = transpile(qc, backend)  # Transpile the circuit

    # Use the Sampler primitive to run the quantum circuit
    job = Sampler(backend).run([transpiled_qc])  # Wrap the circuit in a list and run
    
    # Wait for the job to finish (add timeout or retries to prevent infinite looping)
    max_retries = 5
    retries = 0
    result = None
    while retries < max_retries:
        try:
            result = job.result()
            print(f"Progress: Job completed successfully after {retries + 1} retries.")
            break
        except Exception as e:
            print(f"Error occurred: {e}. Retrying... (Attempt {retries + 1}/{max_retries})")
            retries += 1
            time.sleep(5)  # Delay before retrying
            if retries >= max_retries:
                raise Exception("Max retries reached, job failed to complete.")
    
    # Get the classical register name (this should match the register used in the circuit)
    classical_register = qc.cregs[0].name  # We only have one classical register
    
    # Access the counts for the classical register
    counts = result[0].data[classical_register].get_counts()
    #print(f"Counts: {counts}")  # Print the counts of the random bits generated

    return counts

# Step 3: Generate a quantum password
def generate_password(length=8):
    """
    Generate a random password using quantum randomness.
    """
    print(f"Generating quantum password of length {length}...")
    counts = generate_random_bits(length * 8)  # 8 bits per character
    
    # Extract the bitstring (you can choose the most frequent outcome or just take the first one)
    bit_string = max(counts, key=counts.get)  # Get the most frequent bit string
    print(f"Bit string selected: {bit_string}")  # Print the selected bit string
    password = binary_to_password(bit_string, length)
    return password

# Step 4: Generate and print the quantum password
password = generate_password(length=8)
print(f"Generated Quantum Password: {password}")
