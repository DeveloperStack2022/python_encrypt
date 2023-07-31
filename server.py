from fastapi import FastAPI
from fastapi import UploadFile,File,Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from base64 import b64encode,b64decode
import os 

# Install Crypto
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad,unpad

DIR_COMPLETE = os.path.join(os.getcwd() + '/uploads')
DIR_DECRYPTED = os.path.join(os.getcwd() + '/decrypt')

app = FastAPI() 

origins = [
    "http://localhost:5173",
    "http://192.168.68.127:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
async def root():
    return {"message":"Hello world!"}

# Keys 
key = b'test'
key = pad(key,AES.block_size)


@app.post('/upload_file')
async def upload_file(file: UploadFile = File(...),key_text:str = Form(...)):
    if not file:
        return {"message": "Not file upload!"}
    
    if not os.path.isdir(DIR_COMPLETE):
        os.makedirs('uploads')
    
    key = pad(key_text.encode(),AES.block_size)
    # File
    data = await file.read()
    cipher = AES.new(key,AES.MODE_CFB)
    ciphertext = cipher.encrypt(pad(data,AES.block_size))
    iv = b64encode(cipher.iv).decode('UTF-8')
    ciphertext = b64encode(ciphertext).decode('UTF-8')
    to_write = iv + ciphertext

    file_location = f"uploads/{file.filename}.enc"

    f = open(file_location, "a")
    f.close()

    with open(file_location,'wb') as data:
        data.write(to_write.encode())
    data.close()

    return {
        "url":f'/download/encrypt/{file.filename}.enc',
        'name':f'{file.filename}.enc'
    }

@app.post('/decrypt_file')
async def decrypt_file(file: UploadFile = File(...),key_text:str = Form(...)):

    try: 
        key = pad(key_text.encode(),AES.block_size)

        if not file:
            return {"message": "Not file upload!"}
        
        data = await file.read()
        length = len(data)
        iv = data[:24]
        iv = b64decode(iv)
        ciphertext = data[24:length]
        ciphertext = b64decode(ciphertext)
        cipher = AES.new(key,AES.MODE_CFB,iv)
        decrypted = cipher.decrypt(ciphertext)
        decrypted = unpad(decrypted,AES.block_size)

        if not os.path.isdir(DIR_DECRYPTED):
            os.makedirs('decrypt')

        file_dir = f'{file.filename.split(".")[0]}.{file.filename.split(".")[1]}'
        file_location = f"decrypt/{file_dir}"
        
        

        f = open(file_location, "a")
        f.close()

        with open(file_location,'wb') as data:
            data.write(decrypted)
        data.close()
        
        return  {
        "url":f'/download/{file_dir}',
        'name':f'{file_dir}'
        }
    except(ValueError,KeyError):
        return {"message":f'Password is incorrect'}    

@app.get('/download/encrypt/{filename}')
async def download_decrypt(filename:str):
    file_path = f'uploads/{filename}'

    if os.path.exists(file_path):
        return FileResponse(file_path,filename=filename)
    else:
        return {"error":'File not found'}



@app.get('/download/{filename}')
async def download_file(filename:str):
    file_path = f'decrypt/{filename}'
    
    if os.path.exists(file_path):
        return FileResponse(file_path,filename=filename)
    else:
        return {"error":'File not found'}
    
@app.get('/download/encrypt/success/{filename}')
async def download_encrypt_sucess(filename:str):
    os.remove(os.path.join('uploads',filename))
    return {'status':"ok"}

@app.get('/download/decrypt/success/{filename}')
async def download_dcecrypt_success(filename:str):
    os.remove(os.path.join('decrypt',filename))
    return {'status':'ok'}