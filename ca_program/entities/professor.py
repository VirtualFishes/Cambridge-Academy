class Professor:
    def __init__(self, name, code, document, birthdate, phone, email):
        self.name = name
        self.code = code
        self.document = document
        self.birthdate = birthdate
        self.phone = phone
        self.email = email
        
    def __str__(self):
        return f"{self.name} | Código: {self.code} | Documento: {self.document} | Email: {self.email}"