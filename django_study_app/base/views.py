from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Room, Topic, User, Message
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.db.models import Q
from django.contrib import messages


# Create your views here.


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exit')

    context = {'page': page}
    return render(request, 'login_register.html', context)


def registerPage(request):
    form = MyUserCreationForm()
    
    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Something went wrong!")

    context = {"form": form}
    return render(request, "login_register.html", context)


@login_required(login_url="login")
def LogoutUser(request):
    logout(request)
    return redirect("home")


def home(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q)
        | Q(host__username__icontains=q)
        | Q(name__icontains=q)
    )

    user_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    topics = Topic.objects.all()
    room_count = Room.objects.all()
    context = {"rooms": rooms, "topics": topics, "user_messages": user_messages, 'room_count':room_count}

    return render(request, "home.html", context)


def room(request, pk):
    
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by("-created")
    participants = room.participants.all()
    
    if request.method == "POST":
        message = Message.objects.create(
            user=request.user, room=room, body=request.POST.get("body")
        )
        room.participants.add(request.user)
        return redirect("room", pk=room.id)

    context = {
        "room": room,
        "room_messages": room_messages,
        "participants": participants,
    }
    return render(request, "room.html", context)

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    user_messages = user.message_set.all()
    rooms = user.room_set.all()
    topics = Topic.objects.all()
    context = {'user':user, 'rooms':rooms, 'user_messages':user_messages, 'topics':topics}
    return render(request, 'profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        room = Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        room.participants.add(request.user)
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'room_form.html', context)


@login_required(login_url="login")
def UpdateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    

    if request.method == "POST":
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect("home")

    if request.user != room.host:
        messages(request, "You are not allowed here!")

    context = {"form": form, 'topics':topics}
    return render(request, "room_form.html", context)


@login_required(login_url="login")
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    if request.user != room.host:
        messages(request, "You are not allowed here!")


    if request.method == "POST":
        room.delete()
        return redirect("home")
    return render(request, "delete.html", {"obj": room, "delete": "room"})


@login_required(login_url="login")
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        messages(request, "You are not allowed here!")

    if request.method == "POST":
        message.delete()
        return redirect("home")
    return render(request, "delete.html", {"obj": message})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST ,request.FILES ,instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=request.user.id)
    
    return render(request, 'update-user.html', context={'form':form})
