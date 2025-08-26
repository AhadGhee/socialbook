# Importing shortcuts for rendering templates and redirecting
from django.shortcuts import render, redirect

# Importing Django's built-in User model and auth system (login, logout, authenticate)
from django.contrib.auth.models import User, auth

# To return simple responses (not really used here but available)
from django.http import HttpResponse

# For showing success/error/info messages in templates
from django.contrib import messages

# Importing our models (Profile, Post, LikePost)
from .models import Profile, Post, LikePost

# Decorator to make sure only logged-in users can access certain views
from django.contrib.auth.decorators import login_required

# Django forms library (used for ProfileForm below)
from django import forms
# --------------------------------------------------------------


# Django ModelForm for updating the Profile model
class ProfileForm(forms.ModelForm):
    class Meta:
        # The model this form is based on
        model = Profile
        # Fields we want to expose in the form
        fields = ['profileimg', 'bio', 'location']
        # Custom widgets (HTML input types and CSS classes)
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'shadow-none bg-gray-100'}),
            'location': forms.TextInput(attrs={'class': 'shadow-none bg-gray-100'}),
            'profileimg': forms.FileInput(attrs={'class': 'shadow-none bg-gray-100'}),
        }


# --------------------------------------------------------------
# Home page (feed) view
@login_required(login_url='signin')   # make sure only logged-in users can see feed
def index(request):
    # Get the currently logged-in user object
    user_object = User.objects.get(username=request.user.username)
    
    # Get the Profile that belongs to this user
    user_profile = Profile.objects.get(user=user_object)

    # Get all posts from the database (to show in the feed)
    posts = Post.objects.all()

    # Render index.html and pass profile + posts to the template
    return render(request,'index.html', {'user_profile': user_profile, 'posts': posts})


# --------------------------------------------------------------
# Handle liking a post
@login_required(login_url='signin')   # only logged-in users can like posts
def like_post(request):
    username = request.user.username         # who is liking the post
    post_id = request.GET.get('post_id')     # which post is being liked (from URL query param)

    post = Post.objects.get(id=post_id)      # fetch the post object from DB by its id

    # Try to find an existing LikePost record for this user + post
    # .filter() returns a QuerySet, and .first() returns the first match or None if none found
    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    # CASE 1: If no like exists → create a new LikePost record
    if like_filter is None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)  # create new like entry
        new_like.save()                                                         # save it to DB

        post.no_of_likes = post.no_of_likes + 1   # increment post's like counter
        post.save()                               # save updated post
        return redirect('/')                      # go back to homepage/feed

    # CASE 2: If like already exists → remove it (unlike)
    else:
        like_filter.delete()                       # delete the existing LikePost row

        post.no_of_likes = post.no_of_likes - 1    # decrement post's like counter
        post.save()                                # save updated post
        return redirect('/')                       # go back to homepage/feed
   


# --------------------------------------------------------------
# Handle user signup
def signup(request):
    if request.method == 'POST':   # if form is submitted
        username = request.POST['username']   # get username from form
        email = request.POST['email']         # get email from form
        password = request.POST['password']   # get password from form
        password2 = request.POST['password2'] # confirm password field

        # Check if both passwords match
        if password == password2:
            # Check if email already exists in DB
            if User.objects.filter(email=email).exists():
                messages.info(request, 'This email already exists')
                return redirect('signup')
            
            # Check if username already exists in DB
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username is taken')
                return redirect('signup')
            
            else:
                # Create a new user if no conflicts
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                # Log user in immediately after signup
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                # Create an empty Profile linked to the new user
                Profile.objects.create(user=user)

                # Redirect to settings page so they can update profile
                return redirect('settings')
        else:
            # If passwords do not match
            messages.info(request, 'Password Not Matching')
            return redirect('signup')
    else:
        # If request is GET → just show signup page
        return render(request, 'signup.html')

def profile(request):
    return render(request, 'profile.html')

# --------------------------------------------------------------
# Handle user signin
def signin(request):
    if request.method == 'POST':   # if form is submitted
        username = request.POST['username']   # get username
        password = request.POST['password']   # get password
        
        # Authenticate credentials
        user = auth.authenticate(username=username, password=password)

        if user is not None:   # if credentials are correct
            auth.login(request, user)        # log user in
            return redirect('/')             # send them to homepage
        else:
            # if credentials invalid, show error message
            messages.info(request, 'Credentials Invalid')
            return redirect('/signin')
    else:
        # If request is GET → show login form
        return render(request,'signin.html')
    

# --------------------------------------------------------------
# Handle settings page (profile updates)
@login_required(login_url='signin')
def settings(request):
    try:
        # Try to get the user's profile from DB
        user_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # If profile doesn't exist, create one for this user
        user_profile = Profile.objects.create(user=request.user)
        user_profile.save()

    if request.method == 'POST':   # if updating profile form
        # Bind form with submitted POST data + FILES (image uploads)
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():   # check validation
            form.save()       # save changes to DB
            return redirect('settings')
    else:
        # If GET request, load existing profile into form
        form = ProfileForm(instance=user_profile)

    # Render settings page and send profile + form
    return render(request, 'setting.html', {'user_profile': user_profile, 'form': form})


# --------------------------------------------------------------
# Handle logout
def logout(request):
    auth.logout(request)    # remove session data, log user out
    return redirect('signin')


# --------------------------------------------------------------
# Handle uploading a new post
@login_required(login_url='signin')
def upload(request):
    if request.method == 'POST':   # if form submitted
        user = request.user.username          # get username of uploader
        image = request.FILES.get('image_upload')  # get uploaded image file
        caption = request.POST['caption']     # get caption text

        # Create a new Post record
        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

        return redirect('/')    # redirect back to home after upload
    else:
        return redirect('/')