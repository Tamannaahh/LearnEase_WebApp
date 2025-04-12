from django.shortcuts import redirect, render 
from . forms import *
from django.contrib import messages
from django.views import generic
from .models import Notes
from youtubesearchpython import VideosSearch
from .forms import DashboardForm
import requests
import wikipedia
from django.contrib.auth.decorators import login_required

# Create your views here.

#--------------------------- NOTES PAGE-------------------------------------
def home(request):
    return render(request,'dashboard/home.html')

@login_required
def notes(request):
    if request.method == "POST":
        form = NotesForm(request.POST)
        if form.is_valid():
            notes = Notes(user=request.user,title=request.POST['title'],description=request.POST['description'])
            notes.save()
        messages.success(request,f"Notes Added from {request.user.username} Successfully!")
    else:
        form = NotesForm()
    notes = Notes.objects.filter(user=request.user)
    context = {'notes':notes, 'form':form}
    return render(request,'dashboard/notes.html',context)


@login_required
def delete_note(request,pk=None):
    Notes.objects.get(id=pk).delete()
    return redirect("notes")

class NotesDetailView(generic.DetailView):
    model = Notes
  


#--------------------------- HOMEWORK PAGE-------------------------------------
@login_required
def homework(request):
    if request.method == "POST":
        form = HomeworkForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST['is_finished']
                if finished == 'on':
                    finished = True
                else:
                    finished = False
            except: 
                finished = False

            homeworks = Homework(
                user = request.user,
                subject = request.POST['subject'],
                title = request.POST['title'],
                description = request.POST['description'],
                due = request.POST['due'],
                is_finished = finished
            )
            homeworks.save()
            messages.success(request,f'Homework Added from {request.user.username} Successfully!')
            return redirect('homework')
    else:
        form = HomeworkForm()
    homework = Homework.objects.filter(user=request.user)
    homework_done = len(homework) == 0

    # if len(homework) == 0:
    #     homework_done = True
    # else:
    #     homework_done = False

    context = {
            'homeworks':homework, 
            'homeworks_done':homework_done,
            'form':form,
    }
    return render(request,'dashboard/homework.html',context)

# def update_homework(request,pk=None):
#     homework = Homework.objects.get(id=pk)
#     if homework.is_finished == True:
#         homework.is_finished = False
#     else:
#         homework.is_finished = True
#     homework.save()
#     return redirect('homework')


@login_required
def update_homework(request, pk=None):
    homework = Homework.objects.get(id=pk)
    homework.is_finished = not homework.is_finished
    homework.save()
    messages.success(request, f"Homework status updated successfully!")
    return redirect('homework')

@login_required
def delete_homework(request,pk=None):
    Homework.objects.get(id=pk).delete()
    return redirect("homework") 



#--------------------------- YOUTUBE PAGE---------------------------------

def youtube(request):
    if request.method == "POST":
        form = DashboardForm(request.POST)
        text = request.POST['text']
        video = VideosSearch(text, limit=10)
        result_list = []
        for i in video.result()['result']:
            result_dict = {
                'input': text,
                'title': i['title'],
                'duration': i['duration'],
                'thumbnails': i['thumbnails'][0]['url'], 
                'channel': i['channel']['name'],
                'link': i['link'],
                'views': i['viewCount']['short'],
                'published': i['publishedTime']
            }
            desc = ''
            if i['descriptionSnippet']:
                for j in i['descriptionSnippet']:
                    desc += j['text']
            result_dict['description'] = desc
            result_list.append(result_dict)
        
        context = {
            'form': form,
            'results': result_list
        }
        return render(request, 'dashboard/youtube.html', context)

    else:
        form = DashboardForm()

    context = {'form': form}
    return render(request, 'dashboard/youtube.html', context)




#---------------------------TODO_PAGE---------------------------------
@login_required
def todo(request):
    if request.method == "POST":
        form = TodoForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST.get("is_finished", False)
                if finished == 'on':
                    finished = True
                else:
                    finished = False
            except: 
                finished = False

            new_todo = Todo(
                user=request.user,
                title=request.POST['title'],
                is_finished=finished
            )
            new_todo.save()
            messages.success(request, f'Todo Added from {request.user.username} Successfully!')
    else:
        form = TodoForm()
    
    # Query all todos for the current user
    todo = Todo.objects.filter(user=request.user)

    # Check if there are no todos
    if len(todo) == 0: 
        todos_done = True
    else:
        todos_done = False

    # Pass variables to the template
    context = {
        'form': form,
        'todos': todo,  
        'todos_done': todos_done
    }
    return render(request, 'dashboard/todo.html', context)

@login_required
def update_todo(request, pk=None):
    todo = Todo.objects.get(id=pk)
    if todo.is_finished == True:
        todo.is_finished = False
    else:
        todo.is_finished = True
    todo.save()
    return redirect('todo') 

@login_required
def delete_todo(request,pk=None):
    Todo.objects.get(id=pk).delete()
    return redirect("todo") 



#---------------------------BOOKS_PAGE---------------------------------
def books(request):
    if request.method == "POST":
        form = DashboardForm(request.POST)
        text = request.POST['text']
        url = "https://www.googleapis.com/books/v1/volumes?q=" + text
        r = requests.get(url)
        answer = r.json()

        result_list = []
        for i in range(10):
            # Safely access fields to prevent KeyError or AttributeError
            item = answer['items'][i]['volumeInfo']
            image_links = item.get('imageLinks')  # Can return None

            result_dict = {
                'title': item.get('title'),
                'subtitle': item.get('subtitle'),
                'description': item.get('description'),
                'count': item.get('pageCount'),
                'categories': item.get('categories'),
                'rating': item.get('averageRating'),
                'thumbnail': image_links['thumbnail'] if image_links else None,  # Safely handle None
                'preview': item.get('previewLink')
            }
            result_list.append(result_dict)

        context = {
            'form': form,
            'results': result_list
        }
        return render(request, 'dashboard/books.html', context)

    else:
        form = DashboardForm()

    context = {'form': form}
    return render(request, 'dashboard/books.html', context)


#---------------------------DICTIONARY_PAGE---------------------------------
def dictionary(request):
    if request.method == "POST":
        form = DashboardForm(request.POST)
        text = request.POST['text']
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en_US/{text}"
        r = requests.get(url)
        answer = r.json()
        try:
            phonetics = answer[0]['phonetics'][0].get('text', 'N/A')
            audio = answer[0]['phonetics'][0].get('audio', '')
            definition = answer[0]['meanings'][0]['definitions'][0].get('definition', 'No definition available')
            example = answer[0]['meanings'][0]['definitions'][0].get('example', 'No example available')
            synonyms = answer[0]['meanings'][0]['definitions'][0].get('synonyms', [])

            context = {
                'form': form,
                'input': text,
                'phonetics': phonetics,
                'audio': audio,
                'definition': definition,
                'example': example,
                'synonyms': synonyms,
            }
        except Exception as e:
            context = {
                'form': form,
                'input': text,
                'error': "Could not fetch data. Please try again.",
            }
        return render(request, 'dashboard/dictionary.html', context)
    else:
        form = DashboardForm()
        context = {'form': form}
    return render(request, 'dashboard/dictionary.html', context)


#---------------------------WIKIPEDIA_PAGE---------------------------------
def wiki(request):
    if request.method == "POST":
        text = request.POST['text']
        form = DashboardForm(request.POST)
        search = wikipedia.page(text)
        context = {
                'form': form,
                'title':search.title,
                'link':search.url,
                'details':search.summary
         }
        return render(request, 'dashboard/wiki.html', context)
    else:
        form = DashboardForm()
        context = {
                'form': form
        }
    return render(request, 'dashboard/wiki.html', context)



#---------------------------CONVERSION_PAGE---------------------------------
def conversion(request):
    if request.method == "POST":
        form = ConversionForm(request.POST)
        if request.POST['measurement'] =='length':
            measurement_form = ConversionLengthForm()
            context = {
                'form': form,
                'm_form':measurement_form,
                'input':True
            }
            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST['input']
                answer = ''
                if input and int(input) >= 0:
                    if first == 'yard' and second =='foot':
                        answer = f'{input} yard = {int(input)*3} foot'
                    if first == 'foot' and second =='yard':
                        answer = f'{input} foot = {int(input)/3} yard'
                context = {
                    'form': form,
                    'm_form':measurement_form,
                    'input':True,
                    'answer':answer
                }

        if request.POST['measurement'] =='mass':
            measurement_form = ConversionMassForm()
            context = {
                'form': form,
                'm_form':measurement_form,
                'input':True
            }
            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST['input']
                answer = ''
                if input and int(input) >= 0:
                    if first == 'pound' and second =='kilogram':
                        answer = f'{input} pound = {int(input)*0.453592} kilogram'
                    if first == 'kilogram' and second =='pound':
                        answer = f'{input} kilogram = {int(input)*2.20462} pound'
                context = {
                    'form': form,
                    'm_form':measurement_form,
                    'input':True,
                    'answer':answer
                }
    else:
        form = ConversionForm()
        context = {
            'form': form,
            'input':False
        }
    return render(request, 'dashboard/conversion.html', context)


# --------------------------REGISTRATION_PAGE---------------------------------
def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username =form.cleaned_data.get('username')
            messages.success(request,f"Account Created for {username} Successfully..!!")
            return redirect("login")
    else:
        form = UserRegistrationForm
    context = {
        'form': form
    }
    return render(request, 'dashboard/register.html', context)


# --------------------------PROFILE_PAGE---------------------------------
@login_required
def profile(request):
    homeworks = Homework.objects.filter(is_finished=False, user=request.user)
    todos = Todo.objects.filter(is_finished=False, user=request.user)
    
    # Check if there are any unfinished tasks
    homework_done = len(homeworks) == 0
    todos_done = len(todos) == 0

    context = {
        'homeworks': homeworks,
        'todos': todos,
        'homeworks_done': homework_done,  
        'todos_done': todos_done,
    }

    return render(request, 'dashboard/profile.html', context)


# --------------------------GAMES_PAGE---------------------------------

from django.shortcuts import render
from django.http import HttpResponse
import random

def generate_random_sudoku():
    """Generates a randomized initial Sudoku grid."""
    base_grid = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]
    for _ in range(20):  # Randomly swap numbers in the base grid
        a, b = random.sample(range(1, 10), 2)
        for i in range(9):
            for j in range(9):
                if base_grid[i][j] == a:
                    base_grid[i][j] = b
                elif base_grid[i][j] == b:
                    base_grid[i][j] = a
    return base_grid

def is_valid_sudoku(grid):
    def is_valid_block(block):
        block = [num for num in block if num != 0]
        return len(block) == len(set(block))

    # Check rows
    for row in grid:
        if not is_valid_block(row):
            return False

    # Check columns
    for col in zip(*grid):
        if not is_valid_block(col):
            return False

    # Check 3x3 sub-grids
    for i in range(0, 9, 3):
        for j in range(0, 9, 3):
            block = [
                grid[x][y]
                for x in range(i, i + 3)
                for y in range(j, j + 3)
            ]
            if not is_valid_block(block):
                return False

    return True

def games_view(request):
    error = None
    success = None
    sudoku = generate_random_sudoku()

    if request.method == 'POST':
        if 'reset' in request.POST:
            sudoku = generate_random_sudoku()
        else:
            user_sudoku = []
            for row in range(1, 10):
                user_row = []
                for col in range(1, 10):
                    cell_value = request.POST.get(f"cell_{row}_{col}", "").strip()
                    user_row.append(int(cell_value) if cell_value.isdigit() else 0)
                user_sudoku.append(user_row)

            if any(0 in row for row in user_sudoku):
                error = "Please fill in all cells before checking the solution."
            elif is_valid_sudoku(user_sudoku):
                success = "Congratulations! You solved the Sudoku!"
            else:
                error = "The Sudoku solution is incorrect. Please try again."

    return render(
        request,
        'dashboard/games.html',
        {
            'sudoku': sudoku,
            'error': error,
            'success': success,
            'range': range(1, 10)
        }
    )

# --------------------------CAREER_PAGE---------------------------------

from django.shortcuts import render

def career(request):
    interests = ["AI", "Marketing", "Design", "Cybersecurity", "Finance", "Healthcare", "Education", "Gaming", "Social Media", "E-commerce"]
    abilities = ["Programming", "Data Analysis", "Creative Thinking", "Management", "Sales", "Writing", "Problem Solving", "Teamwork", "Leadership", "Content Creation"]
    preferences = ["Remote Work", "Startup Enthusiast", "Flexible Hours", "Travel", "High Salary", "Job Security", "Freelancing", "Diversity", "Innovation", "Work-Life Balance"]

    if request.method == "POST":
        # Collect selected checkboxes
        selected_interests = request.POST.getlist("interests")
        selected_abilities = request.POST.getlist("abilities")
        selected_preferences = request.POST.getlist("preferences")

        if not selected_interests and not selected_abilities and not selected_preferences:
            return render(request, 'dashboard/career.html', {
                'error': 'Please select at least one option.',
                'interests': interests,
                'abilities': abilities,
                'preferences': preferences
            })

        # Example of mapping checkbox selections to jobs
        job_results = []
        if "AI" in selected_interests or "Programming" in selected_abilities:
            job_results.append({
                "title": "AI Engineer",
                "company": "Google",
                "location": "Global",
                "link": "https://www.google.com/about/careers/applications/jobs/results"
            })

        if "Marketing" in selected_interests or "Content Creation" in selected_abilities:
            job_results.append({
                "title": "Digital Marketing Specialist",
                "company": "Google",
                "location": "Remote",
                "link": "https://www.google.com/about/careers/applications/jobs/results"
            })

        if "Design" in selected_interests or "Creative Thinking" in selected_abilities:
            job_results.append({
                "title": "Graphic Designer",
                "company": "Google",
                "location": "Global",
                "link": "https://www.google.com/about/careers/applications/jobs/results"
            })

        if "Data Analysis" in selected_abilities or "Remote Work" in selected_preferences:
            job_results.append({
                "title": "Data Analyst",
                "company": "Google",
                "location": "Remote",
                "link": "https://www.google.com/about/careers/applications/jobs/results"
            })

        if "Flexible Hours" in selected_preferences or "Startup Enthusiast" in selected_preferences:
            job_results.append({
                "title": "Startup Growth Manager",
                "company": "Google",
                "location": "Flexible",
                "link": "https://www.google.com/about/careers/applications/jobs/results"
            })

        if not job_results:
            return render(request, 'dashboard/career.html', {
                'error': 'No suitable jobs found based on your selections.',
                'interests': interests,
                'abilities': abilities,
                'preferences': preferences
            })

        return render(request, 'dashboard/career.html', {
            'jobs': job_results,
            'interests': interests,
            'abilities': abilities,
            'preferences': preferences
        })

    return render(request, 'dashboard/career.html', {
        'interests': interests,
        'abilities': abilities,
        'preferences': preferences
    })


