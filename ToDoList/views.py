from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ToDoItem
from .forms import ToDoItemForm

@login_required
def home(request):
    items = ToDoItem.objects.filter(user=request.user)
    return render(request, 'ToDoList/home.html', {'items': items})

@login_required
def add_item(request):
    if request.method == 'POST':
        form = ToDoItemForm(request.POST)
        if form.is_valid():
            todo_item = form.save(commit=False)
            todo_item.user = request.user
            todo_item.save()
            return redirect('todo:home')
    else:
        form = ToDoItemForm()
    return render(request, 'ToDoList/add_item.html', {'form': form})

@login_required
def edit_item(request, item_id):
    item = get_object_or_404(ToDoItem, id=item_id, user=request.user)
    if request.method == 'POST':
        form = ToDoItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            print("Form is valid and saved")  # Debug: Print when form is valid and saved
            return redirect('todo:home')
        else:
            print("Form is not valid")  # Debug: Print when form is not valid
            print(form.errors)  # Debug: Print form errors if form is not valid
    else:
        form = ToDoItemForm(instance=item)
    return render(request, 'ToDoList/edit_item.html', {'form': form, 'item': item})

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(ToDoItem, id=item_id, user=request.user)
    if request.method == 'POST':
        item.delete()
        return redirect('todo:home')
    return render(request, 'ToDoList/delete_item.html', {'item': item})