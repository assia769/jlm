# api/views.py

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Sum, Avg, Count
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import *
import json

# Vues publiques (pas d'authentification requise)
@api_view(['GET'])
@permission_classes([AllowAny])
def home_stats(request):
    """Statistiques pour la page d'accueil"""
    stats = {
        'total_clients': Client.objects.filter(Actif=True).count(),
        'total_volume_traite': SourceEau.objects.aggregate(Sum('Volume_Fournit'))['Volume_Fournit__sum'] or 0,
        'installations_actives': Pompe.objects.filter(Etat='ON').count(),
        'satisfaction_moyenne': Feedback.objects.aggregate(Avg('Note'))['Note__avg'] or 0,
    }
    return Response(stats)

@api_view(['GET'])
@permission_classes([AllowAny])
def positive_feedback(request):
    """Récupérer les feedbacks positifs (note >= 4)"""
    feedbacks = Feedback.objects.filter(Note__gte=4).select_related('ID_Client').order_by('-Date_Feedback')[:10]
    feedback_data = []
    for feedback in feedbacks:
        feedback_data.append({
            'id': feedback.ID_Feedback,
            'commentaire': feedback.Commentaire,
            'note': feedback.Note,
            'date': feedback.Date_Feedback,
            'client_nom': feedback.ID_Client.Nom_Client
        })
    return Response(feedback_data)

# Authentification
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        
        # Vérifier si c'est un admin
        try:
            admin = Administrateur.objects.get(user=user)
            return Response({
                'success': True,
                'user_type': 'admin',
                'user_id': admin.ID_Admin,
                'name': admin.Nom_Admin
            })
        except Administrateur.DoesNotExist:
            pass
        
        # Vérifier si c'est un client
        try:
            client = Client.objects.get(user=user)
            return Response({
                'success': True,
                'user_type': 'client',
                'user_id': client.ID_Client,
                'name': client.Nom_Client
            })
        except Client.DoesNotExist:
            pass
            
        return Response({'success': False, 'message': 'Utilisateur non trouvé'})
    
    return Response({'success': False, 'message': 'Identifiants incorrects'})

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    try:
        data = request.data
        
        # Créer l'utilisateur Django
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password'],
            first_name=data['nom']
        )
        
        # Créer le client
        client = Client.objects.create(
            Nom_Client=data['nom'],
            Email=data['email'],
            Téléphone=data.get('telephone', ''),
            Adresse=data.get('adresse', ''),
            Motdepasse=data['password'],
            user=user
        )
        
        return Response({'success': True, 'message': 'Compte créé avec succès'})
    except Exception as e:
        return Response({'success': False, 'message': str(e)})

@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({'success': True})

# Vues Admin
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    try:
        admin = Administrateur.objects.get(user=request.user)
    except Administrateur.DoesNotExist:
        return Response({'error': 'Non autorisé'}, status=403)
    
    # Statistiques générales
    stats = {
        'total_clients': Client.objects.count(),
        'clients_actifs': Client.objects.filter(Actif=True).count(),
        'total_reservoirs': Reservoir.objects.count(),
        'pompes_actives': Pompe.objects.filter(Etat='ON').count(),
        'alertes_non_resolues': Alerte.objects.filter(Statut='Non résolu').count(),
        'revenus_mensuels': Facture.objects.filter(
            Date_Facture__gte=datetime.now().replace(day=1)
        ).aggregate(Sum('Montant_Total'))['Montant_Total__sum'] or 0
    }
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def water_levels(request):
    """Niveaux d'eau des réservoirs"""
    reservoirs = Reservoir.objects.all()
    data = []
    for reservoir in reservoirs:
        percentage = (reservoir.Volume_Disponible / reservoir.Volume_Max) * 100
        data.append({
            'nom': reservoir.Nom_Reservoir,
            'niveau': percentage,
            'volume_disponible': reservoir.Volume_Disponible,
            'volume_max': reservoir.Volume_Max
        })
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def energy_production(request):
    """Production d'énergie"""
    energies = Energie.objects.values('Type_Energie').annotate(
        total_production=Sum('Production_Mensuelle'),
        total_consommation=Sum('Consommation_Mensuelle')
    )
    return Response(list(energies))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def distribution_monthly(request):
    """Distribution mensuelle"""
    from django.db.models import Extract
    
    distributions = Distribution.objects.filter(
        Date_Distribution__gte=datetime.now() - timedelta(days=365)
    ).extra(
        select={'mois': "DATE_FORMAT(Date_Distribution, '%%Y-%%m')"}
    ).values('mois').annotate(
        total_volume=Sum('Volume_Distribué')
    ).order_by('mois')
    
    return Response(list(distributions))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pump_status(request):
    """État des pompes"""
    pompes = Pompe.objects.all()
    data = []
    for pompe in pompes:
        data.append({
            'nom': pompe.Nom_Pompe,
            'etat': pompe.Etat,
            'debit': pompe.Débits,
            'reservoir': pompe.ID_Reservoir.Nom_Reservoir
        })
    return Response(data)

# Vues Client
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_dashboard(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return Response({'error': 'Non autorisé'}, status=403)
    
    # Historique des commandes
    distributions = Distribution.objects.filter(ID_Client=client).order_by('-Date_Distribution')[:10]
    commandes = []
    for dist in distributions:
        commandes.append({
            'date': dist.Date_Distribution,
            'volume': dist.Volume_Distribué,
            'id': dist.ID_Distribution
        })
    
    # Factures
    factures = Facture.objects.filter(ID_Client=client).order_by('-Date_Facture')[:5]
    factures_data = []
    for facture in factures:
        factures_data.append({
            'id': facture.ID_Facture,
            'date': facture.Date_Facture,
            'montant': facture.Montant_Total,
            'statut': facture.Statut_Paiement
        })
    
    return Response({
        'client_info': {
            'nom': client.Nom_Client,
            'email': client.Email,
            'solde': client.Solde,
            'volume_consomme': client.Volume_Consommé
        },
        'commandes': commandes,
        'factures': factures_data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_feedback(request):
    try:
        client = Client.objects.get(user=request.user)
        
        feedback = Feedback.objects.create(
            Commentaire=request.data['commentaire'],
            Note=request.data['note'],
            Date_Feedback=datetime.now().date(),
            ID_Client=client
        )
        
        return Response({'success': True, 'message': 'Feedback ajouté avec succès'})
    except Client.DoesNotExist:
        return Response({'error': 'Non autorisé'}, status=403)
    except Exception as e:
        return Response({'error': str(e)}, status=400)