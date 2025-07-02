# api/models.py

from django.db import models
from django.contrib.auth.models import User

class Client(models.Model):
    ID_Client = models.AutoField(primary_key=True)
    Nom_Client = models.CharField(max_length=100)
    Email = models.EmailField(unique=True)
    Téléphone = models.CharField(max_length=15, blank=True)
    Adresse = models.TextField(blank=True)
    Volume_Consommé = models.FloatField(default=0.0)
    Solde = models.FloatField(default=0.0)
    Statut_Paiement = models.CharField(max_length=50, default='Non payé')
    Actif = models.BooleanField(default=True)
    Motdepasse = models.CharField(max_length=255)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.Nom_Client

class SourceEau(models.Model):
    ID_Source = models.AutoField(primary_key=True)
    Type_Source = models.CharField(max_length=50)
    Nom_Source = models.CharField(max_length=100)
    Adresse = models.TextField(blank=True)
    Contact = models.CharField(max_length=50, blank=True)
    Qualité_Eau = models.CharField(max_length=50)
    Volume_Fournit = models.FloatField()

    def __str__(self):
        return self.Nom_Source

class Reservoir(models.Model):
    ID_Reservoir = models.AutoField(primary_key=True)
    Nom_Reservoir = models.CharField(max_length=100)
    Volume_Max = models.FloatField()
    Volume_Disponible = models.FloatField()
    ID_Source = models.ForeignKey(SourceEau, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.Nom_Reservoir

class Pompe(models.Model):
    ID_Pompe = models.AutoField(primary_key=True)
    Nom_Pompe = models.CharField(max_length=100)
    Etat = models.CharField(max_length=50, default='OFF')
    Débits = models.FloatField()
    ID_Reservoir = models.ForeignKey(Reservoir, on_delete=models.CASCADE)

    def __str__(self):
        return self.Nom_Pompe

class Energie(models.Model):
    ID_Energie = models.AutoField(primary_key=True)
    Type_Energie = models.CharField(max_length=50)
    Production_Mensuelle = models.FloatField()
    Consommation_Mensuelle = models.FloatField()
    ID_Pompe = models.ForeignKey(Pompe, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.Type_Energie} - {self.ID_Pompe}"

class Filtration(models.Model):
    ID_Filtration = models.AutoField(primary_key=True)
    Type_Filtre = models.CharField(max_length=100)
    Efficacité = models.FloatField()
    Date_Dernière_Maintenance = models.DateField()
    ID_Pompe = models.ForeignKey(Pompe, on_delete=models.CASCADE)

    def __str__(self):
        return self.Type_Filtre

class Distribution(models.Model):
    ID_Distribution = models.AutoField(primary_key=True)
    Date_Distribution = models.DateField()
    Volume_Distribué = models.FloatField()
    ID_Client = models.ForeignKey(Client, on_delete=models.CASCADE)
    ID_Pompe = models.ForeignKey(Pompe, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Distribution {self.ID_Distribution}"

class Facture(models.Model):
    ID_Facture = models.AutoField(primary_key=True)
    Date_Facture = models.DateField()
    Montant_Total = models.FloatField()
    Statut_Paiement = models.CharField(max_length=50, default='Non payé')
    ID_Client = models.ForeignKey(Client, on_delete=models.CASCADE)
    ID_Distribution = models.ForeignKey(Distribution, on_delete=models.CASCADE)

    def __str__(self):
        return f"Facture {self.ID_Facture}"

class Alerte(models.Model):
    ID_Alerte = models.AutoField(primary_key=True)
    Message = models.TextField()
    Date_Alerte = models.DateTimeField()
    Statut = models.CharField(max_length=50, default='Non résolu')
    Type_alerte = models.CharField(max_length=50)
    ID_Pompe = models.ForeignKey(Pompe, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Alerte {self.ID_Alerte}"

class Feedback(models.Model):
    ID_Feedback = models.AutoField(primary_key=True)
    Commentaire = models.TextField()
    Note = models.FloatField()
    Date_Feedback = models.DateField()
    ID_Client = models.ForeignKey(Client, on_delete=models.CASCADE)

    def __str__(self):
        return f"Feedback {self.ID_Feedback}"

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(Note__gte=0) & models.Q(Note__lte=5), name='note_range')
        ]

class Administrateur(models.Model):
    ID_Admin = models.AutoField(primary_key=True)
    Nom_Admin = models.CharField(max_length=100)
    Email = models.EmailField(unique=True)
    Mot_de_passe = models.CharField(max_length=255)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.Nom_Admin