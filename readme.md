# Emotorad Backend Task: Identity Reconciliation


## Installation

1. **Clone the repository**

   ```sh
   git clone https://github.com/Swejan17/EMotorad_Identity_Reconciliation.git
   cd EMotorad_Identity_Reconciliation
   ```

2. **Create a virtual environment (optional but recommended)**

   ```sh
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**

   ```sh
   pip install -r requirements.txt
   ```

## Running the Application

To start the FastAPI application with Uvicorn, run:

```sh
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

- `--host 127.0.0.1`: Makes the server accessible on the local network.
- `--port 8000`: Specifies the port.
- `--reload`: Enables automatic reloading on code changes (useful for development).

The API will be available at:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Redoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Running Tests

The project includes tests using `pytest`. To run the tests, execute:

```sh
pytest
```

## GitHub Actions CI

This project includes a GitHub Actions workflow for automatic testing. On every push or pull request, the tests will run automatically.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -m "Added new feature"`).
5. Push to the branch (`git push origin feature-branch`).
6. Open a Pull Request.

## License

This project is licensed under the MIT License.

