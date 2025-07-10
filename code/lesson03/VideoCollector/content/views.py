# VideoCollector/content/views.py
import more_itertools
from django.core.paginator import Paginator
from content.models import Category, Video
from django.shortcuts import get_object_or_404, render
from django import forms
from django.db.models import Q


VideoForm = forms.modelform_factory(
    Video,
    fields=["youtube_id", "title", "author", "view_count"],
)


def home(request):
    categories = Category.objects.all()
    data = {"rows": more_itertools.chunked(categories, 3)}

    return render(request, "home.html", data)


def category(request, name):
    category = get_object_or_404(Category, name__iexact=name)
    if request.method == "POST":
        form = VideoForm(request.POST)
        if form.is_valid():
            video = form.save()
            video.categories.add(category)
    else:
        form = VideoForm()
    videos = Video.objects.filter(categories=category)
    data = {"category": category, "rows": more_itertools.chunked(videos, 3), "form": form}

    return render(request, "category.html", data)


def play_video(request, video_id):
    data = {"video": get_object_or_404(Video, id=video_id)}

    return render(request, "play_video.html", data)


def feed(request):
    videos = Video.objects.all()
    
    paginator = Paginator(videos, 2)
    
    # Récupère le numéro de page depuis les paramètres GET (défaut: page 1)
    page_num = int(request.GET.get("page", 1))
    
    # Validation du numéro de page pour éviter les erreurs
    if page_num < 1:
        page_num = 1  # Si négatif, retourne à la page 1
    elif page_num > paginator.num_pages:
        page_num = paginator.num_pages  # Si trop grand, va à la dernière page
    
    # Récupère l'objet Page correspondant au numéro demandé
    page = paginator.page(page_num)
    
    # Prépare les données pour le template
    data = {
        "videos": page.object_list,      # Les vidéos de la page actuelle
        "more_videos": page.has_next(),  # Booléen: y a-t-il d'autres pages après ?
        "next_page": page_num + 1        # Numéro de la page suivante pour le bouton "Load More"
    }
    
    if request.htmx:
        import time
        time.sleep(2)
        return render(request, "partials/feed_results.html", data)
    
    return render(request, "feed.html", data)


def add_video_form(request, name):
    category = get_object_or_404(Category, name__iexact=name)
    data = {"category": category}

    return render(request, "partials/add_video_form.html", data)


def add_video_link(request, name):
    category = get_object_or_404(Category, name__iexact=name)
    data = {"category": category}

    return render(request, "partials/add_video_link.html", data)


def search(request):
    search_text = request.GET.get("search_text", "")
    
    videos = Video.objects.none()
    
    if search_text:
        parts = search_text.split()
        # Commence avec le premier mot : recherche dans titre OU auteur
        q = Q(title__icontains=parts[0]) | Q(author__icontains=parts[0])
        # Pour chaque mot suivant, ajoute une condition OR
        # Ex: "python django" → trouve si titre/auteur contient "python" OU "django"
        for part in parts[1:]:
            q |= Q(title__icontains=part) | Q(author__icontains=part)
        videos = Video.objects.filter(q).distinct()
    
    data = {"search_text": search_text, "videos": videos}
    
    if request.htmx:
        return render(request, "partials/search_results.html", data)

    return render(request, "search.html", data)
