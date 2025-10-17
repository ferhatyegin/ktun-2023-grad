#Convert Image to Base64
from os import path,makedirs,remove
from base64 import b64decode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from werkzeug.exceptions import BadRequest
from re import match,sub
from pypdf import PdfReader,PdfWriter
from ast import literal_eval
from shutil import rmtree

#Decode Image & Save It To the Uploads Folder
def upload(file,name):
    try:
        image_data = sub('^data:image/.+;base64,', '', file)
        im = Image.open(BytesIO(b64decode(image_data)))
        if "_banner" in name:
            img_path = "static/img/show_banners"
            resized = im.resize((1400, 400))
            resized.save(f"{img_path}/{name}.png")
            return "success"
        img_path = "static/img/shows/" + name
        makedirs(img_path, exist_ok=True) # create directory if it doesn't exist
        im.save(f"{img_path}/{name}.png")
        thumbnail = im.copy()
        thumbnail = thumbnail.resize((250,350)) # assign the resized image to the variable
        thumbnail.save(f"{img_path}/{name}_thumbnail.png")
        return name
    except Exception as e:
        raise BadRequest(e)
    
def multi_upload(files, id, photo_count):
    try:
        names = []
        photo_count += 1
        for file in files:
            image_data = file.split(',')[1] # remove the data:image/*;base64, prefix
            name = str(id) + "_" + str(photo_count) # generate a random filename
            img_path = f"static/img/shows/{id}"
            makedirs(img_path, exist_ok=True) # create directory if it doesn't exist
            im = Image.open(BytesIO(b64decode(image_data)))
            resize = im.resize((400, 250))
            resize.save(f"{img_path}/{name}.png")
            names.append(name)
            photo_count += 1
        return names
    except Exception as e:
        raise BadRequest(e)

def remove_game_photos(id):
    try:
        photo_path = f"static/img/shows/{id}"
        banner_path = f"static/img/show_banners/{id}_banner.png"
        if path.exists(photo_path):
            rmtree(photo_path)
        if path.exists(banner_path):
            remove(banner_path)
        return True
    except Exception as e:
        raise BadRequest(e)
    
def remove_photo(photo_list):
    try:
        #Name is going to be a list of names
        for name in photo_list:
            
            if "_banner" in name:
                remove(f"static/img/show_banners/{name}.png")
                return True
            
            if "_" not in name:
                remove(f"static/img/shows/{name}/{name}.png")
                thumbnail_path = f"static/img/shows/{name}/{name}_thumbnail.png"
                remove(thumbnail_path)
                return True
            
            id = name.split("_")[0]
            photo_path = f"static/img/shows/{id}/{name}.png"
            remove(photo_path)
            
        return True
        
    except Exception as e:
        raise BadRequest(e)
#Check If a File With Same Name Exists
BASE_DIR = path.dirname(__file__)
def check_file(name, counter=1, original_name=None,upload_folder=BASE_DIR+"\\uploads"):
    flag = path.isfile(upload_folder+"\\"+name+".png")
    if flag:
        if original_name is None:
            original_name = name
        name = original_name + "_" + str(counter)
        counter += 1
        return check_file(name, counter,original_name)
    return name

def resize_image(image, size=(250, 350)):
    im = Image.open(image)
    im.resize(size)
    return im


def generate_tickets_pdf(show_name, session_date, session_time, user_id, ticket_data):
    # Create the folders for the user and session IDs
    user_folder = path.join('static', 'doc', 'ticket', user_id)
    session_folder = path.join(user_folder, ticket_data["session_id"])
    makedirs(session_folder, exist_ok=True)
    ticket_file = f'{session_folder}/tickets.pdf'

    # Load the existing PDF or create a new one
    if path.exists(ticket_file):
        output_pdf = PdfReader(open(ticket_file, 'rb'))
        new_pdf = PdfWriter()
        new_pdf.append_pages_from_reader(output_pdf)
    else:
        new_pdf = PdfWriter()

    # Generate a new ticket page
    ticket_pages = create_ticket_page(show_name, session_date, session_time,ticket_data)

    # Add the ticket page to the PDF
    for page in ticket_pages:
        new_pdf.add_page(page)

    # Save the updated PDF file
    with open(ticket_file, 'wb') as f:
        new_pdf.write(f)

def create_ticket_page(show_name, session_date, session_time, ticket_data):
    ticket_pages = []
    font_path = path.join('static', 'Sancreek-Regular.ttf')
    font = ImageFont.truetype(font_path, size=40)

    hall = ticket_data['hall']
    seats = literal_eval(ticket_data['seats'])
    template_path = path.join('static', 'ticket_template.png')
    
    for seat in seats:
        ticket_page = Image.open(template_path)  # Create a new ticket page for each seat
        draw = ImageDraw.Draw(ticket_page)

        data = calculate_name_position(show_name, font_path, template_path)
        
        # Add text to the ticket page
        draw.text((data[0], data[1]), data[2].strip(), fill="rgba(248,212,64,255)", font=data[3])
        draw.text((390, 257), f'{session_date}', fill='white', font=font)
        draw.text((635, 251), '|', fill='white', font=font)
        draw.text((672, 257), f'{session_time}', fill='white', font=font)

        # Add ticket data
        draw.text((920, 300), f'{seat}', fill='black', font=font)
        draw.text((1015, 294), '|', fill='black', font=font)
        draw.text((1045, 300), f'{hall}', fill='black', font=font)

        # Convert image object to PDF
        pdf_buffer = BytesIO()
        ticket_page.save(pdf_buffer, format='PDF')

        # Create a PageObject from the byte buffer
        pdf_buffer.seek(0)
        ticket_page_obj = PdfReader(pdf_buffer).pages[0]
        ticket_pages.append(ticket_page_obj)

    return ticket_pages

def calculate_name_position(show_name, font_path, template_path):
    # Define the boundaries
    x_min = 400
    y_min = 50
    x_max = 790
    y_max = 255
    
    # Calculate the maximum allowed width and height for the text
    max_width = x_max - x_min
    max_height = y_max - y_min
    
    font_size = 100
    name_font = ImageFont.truetype(font_path, font_size)
    
    # Loop to find the suitable font size
    while name_font.getsize(show_name)[0] > max_width or name_font.getsize(show_name)[1] > max_height:
        font_size -= 1
        name_font = ImageFont.truetype(font_path, font_size)
        
    ticket_page = Image.open(template_path)  # Path to your background image
    draw = ImageDraw.Draw(ticket_page)
                
    # Calculate the position to place the text
    text_width, text_height = draw.textsize(show_name, font=name_font)
    text_x = x_min
    text_y = y_min
    
    # Split the show name into words
    words = show_name.split()
    
    # Iterate over the words and place them within the boundaries
    current_line = ""
    for word in words:
        line = current_line + word + " "
        line_width, line_height = draw.textsize(line, font=name_font)
        if line_width > max_width:
            # The line exceeds the width, move to the next line
            draw.text((text_x, text_y), current_line.strip(), font=name_font, fill="black")
            text_y += line_height
            #current_line = ""  # Reset the current line
        current_line += word + " "
    
    # Draw the last line of text
    draw.text((text_x, text_y), current_line.strip(), font=name_font, fill="black")
            
    return (text_x, text_y, current_line, name_font)

#Mail Address Validator Using RE
def mail_val(mail):
    #Check mail properties using regular expressions
    check = "^[a-zA-Z0-9-_.]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
    if match(check,mail):
        return True
    return False



        

