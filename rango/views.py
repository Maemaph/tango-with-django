from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from rango import Category
from rango import Page
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from datetime import datetime

def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', '1'))

    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        request.session['last_visit'] = str(datetime.now())
    else:
        visits = 1
        request.session['last_visit'] = last_visit_cookie

    request.session['visits'] = visits


def index(request):
    request.session.set_test_cookie()
    # Query the database for a list of all categories in descending order
    # Retrieve top 5 only - or all if less than 5 and place in our context dict

    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    context_dict = {'categories': category_list, 'pages': page_list}

    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']

    # Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.
    response = render(request, 'rango/index.html', context=context_dict)
    return response


def about(request):
    if request.session.test_cookie_worked():
        print("TEST COOKIE WORKED")
        request.session.delete_test_cookie()

    about_dict = {'name': "Olatunji Mafe"}
    print(request.method)
    print(request.user)
    return render(request, 'rango/about.html', context=about_dict)

def show_category(request, category_name_slug):
    # create the context dictionary
    context_dict = {}

    try:
        # Check category name slug, if not available
        # .get method raise an exception
        category = Category.objects.get(slug=category_name_slug)

        # Retrieve all associated pages
        pages = Page.objects.filter(category=category)

        # Adds results list to the template context under name pages
        context_dict['pages'] = pages

        # Also adds to the category to verify the category exists
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category
        # 'No category' will be displayed
        context_dict['category'] = None
        context_dict['pages'] = None

    return render(request, 'rango/category.html', context_dict)

def add_category(request):
    form = CategoryForm()

    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            cat = form.save(commit=True)
            print(cat, cat.slug)
            return index(request)
        else:
            print(form.errors)

    return render(request, 'rango/add_category.html', {'form': form})

def add_page(request, category_name_slug):
    category = Category.objects.get(slug=category_name_slug)
    """try:
        
    except Category.DoesNotExist:
        # category = None
    """
    form = PageForm()
    if request.method == 'POST':
       form = PageForm(request.POST)
       if form.is_valid():
           if category:
               page = form.save(commit=False)
               page.category = category
               page.views = 0
               page.save()
               return show_category(request, category_name_slug)
           else:
               print(form.errors)

    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context_dict)

def register(request):
    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()

            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

                profile.save()
                registered = True
        else:
            print(user_form.errors, profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(request, 'rango/register.html',
                  {'user_form': user_form,
                   'profile_form': profile_form,
                   'registered': registered})

def user_login(request):
    if request.method == 'POST':
        # get user details from login form

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponse("Your Rango account is disabled.")
        else:
            print("Invalid login details: {0}, {1}".format(username, password))
            return HttpResponse("Invalid login details supplied.")

    else:
        return render(request, 'rango/login.html', {})

def some_view(request):
    if not request.user.is_authenticated():
        return HttpResponse("You are logged in.")
    else:
        return HttpResponse("You are not logged in.")

@login_required
def restricted(request):
    return render(request, 'rango/restricted.html', {})

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))
