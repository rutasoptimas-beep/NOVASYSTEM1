from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os, re, json, random, string

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'neonthread-secret-2025')

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///novasystem.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ── MODELOS ──────────────────────────────────────────────────

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id            = db.Column(db.Integer, primary_key=True)
    nombre        = db.Column(db.String(80),  nullable=False)
    apellido      = db.Column(db.String(80),  nullable=False)
    username      = db.Column(db.String(50),  unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    telefono      = db.Column(db.String(20),  nullable=False)
    creado_en     = db.Column(db.DateTime,    default=datetime.utcnow)
    pedidos       = db.relationship('Pedido', backref='usuario', lazy=True)

    def set_password(self, p): self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id          = db.Column(db.Integer, primary_key=True)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    folio       = db.Column(db.String(12), unique=True, nullable=False)
    total       = db.Column(db.Float, nullable=False)
    items_json  = db.Column(db.Text, nullable=False)
    creado_en   = db.Column(db.DateTime, default=datetime.utcnow)
    status      = db.Column(db.String(20), default='confirmado')

@login_manager.user_loader
def load_user(uid): return Usuario.query.get(int(uid))

# ── PRODUCTOS (catálogo estático con 20 por sección) ─────────

PRODUCTOS = {
    'abrigos': [
        {'id':1,  'nombre':'Abrigo Camel Oversize',       'precio':2890, 'tallas':['XS','S','M','L','XL'], 'img':'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=600&q=80&fit=crop', 'categoria':'abrigos'},
        {'id':2,  'nombre':'Trench Coat Beige',            'precio':3200, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=600&q=80&fit=crop', 'categoria':'abrigos'},
        {'id':3,  'nombre':'Abrigo Lana Gris Marengo',    'precio':3850, 'tallas':['XS','S','M','L'],       'img':'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80&fit=crop', 'categoria':'abrigos'},
        {'id':4,  'nombre':'Coat Negro Estructurado',      'precio':4100, 'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=600&q=80&fit=crop', 'categoria':'abrigos'},
        {'id':5,  'nombre':'Abrigo Cuadros Vintage',       'precio':2650, 'tallas':['XS','S','M'],           'img':'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&q=80&fit=crop', 'categoria':'abrigos'},
        {'id':6,  'nombre':'Maxi Coat Crema',              'precio':4500, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&q=80&fit=crop', 'categoria':'abrigos'},
        {'id':7,  'nombre':'Abrigo Borreguillo Blanco',    'precio':3300, 'tallas':['XS','S','M','L','XL'], 'img':'https://images.unsplash.com/photo-1550614000-4895a10e1bfd?w=600&q=80&fit=crop', 'categoria':'abrigos'},
        {'id':8,  'nombre':'Double Breasted Marino',       'precio':3700, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80&fit=crop', 'categoria':'abrigos'},
        {'id':9,  'nombre':'Abrigo Terciopelo Bordo',      'precio':3950, 'tallas':['XS','S','M'],           'img':'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&q=80&fit=crop', 'categoria':'abrigos'},
        {'id':10, 'nombre':'Cape Coat Gris Perla',         'precio':2990, 'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=600&q=80&fit=crop', 'categoria':'abrigos'},
        {'id':11, 'nombre':'Abrigo Paño Chocolate',        'precio':3150, 'tallas':['XS','S','M','L'],       'img':'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=600&q=80&fit=crop&crop=top', 'categoria':'abrigos'},
        {'id':12, 'nombre':'Belted Wool Coat',             'precio':4200, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=600&q=80&fit=crop&crop=top', 'categoria':'abrigos'},
        {'id':13, 'nombre':'Abrigo Estampado Animal',      'precio':3600, 'tallas':['XS','S','M'],           'img':'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80&fit=crop&crop=top', 'categoria':'abrigos'},
        {'id':14, 'nombre':'Abrigo Pata de Gallo',         'precio':2800, 'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=600&q=80&fit=crop&crop=top', 'categoria':'abrigos'},
        {'id':15, 'nombre':'Oversized Blazer Coat',        'precio':3400, 'tallas':['XS','S','M','L'],       'img':'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&q=80&fit=crop&crop=top', 'categoria':'abrigos'},
        {'id':16, 'nombre':'Abrigo Efecto Piel Beige',     'precio':4800, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&q=80&fit=crop&crop=top', 'categoria':'abrigos'},
        {'id':17, 'nombre':'Teddy Bear Coat Caramel',      'precio':3250, 'tallas':['XS','S','M','L','XL'], 'img':'https://images.unsplash.com/photo-1550614000-4895a10e1bfd?w=600&q=80&fit=crop&crop=top', 'categoria':'abrigos'},
        {'id':18, 'nombre':'Abrigo Asimétrico Negro',      'precio':5100, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80&fit=crop&crop=top', 'categoria':'abrigos'},
        {'id':19, 'nombre':'Wool Blend Coat Ivory',        'precio':3750, 'tallas':['XS','S','M'],           'img':'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&q=80&fit=crop&crop=top', 'categoria':'abrigos'},
        {'id':20, 'nombre':'Abrigo Militar Verde',         'precio':2950, 'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=600&q=80&fit=crop&crop=top', 'categoria':'abrigos'},
    ],
    'sueteres': [
        {'id':21, 'nombre':'Suéter Trenzado Crema',        'precio':890,  'tallas':['XS','S','M','L'],       'img':'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&q=80&fit=crop', 'categoria':'sueteres'},
        {'id':22, 'nombre':'Sweater Oversized Gris',       'precio':750,  'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=600&q=80&fit=crop&crop=bottom', 'categoria':'sueteres'},
        {'id':23, 'nombre':'Turtleneck Negro',             'precio':680,  'tallas':['XS','S','M','L','XL'], 'img':'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80&fit=crop&crop=bottom', 'categoria':'sueteres'},
        {'id':24, 'nombre':'Cardigan Largo Camel',         'precio':1100, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=600&q=80&fit=crop&crop=bottom', 'categoria':'sueteres'},
        {'id':25, 'nombre':'Suéter Mohair Rosa',           'precio':950,  'tallas':['XS','S','M'],           'img':'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&q=80&fit=crop&crop=bottom', 'categoria':'sueteres'},
        {'id':26, 'nombre':'Knit Polo Marfil',             'precio':820,  'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&q=80&fit=crop&crop=bottom', 'categoria':'sueteres'},
        {'id':27, 'nombre':'Suéter Crop Beige',            'precio':720,  'tallas':['XS','S','M'],           'img':'https://images.unsplash.com/photo-1550614000-4895a10e1bfd?w=600&q=80&fit=crop&crop=bottom', 'categoria':'sueteres'},
        {'id':28, 'nombre':'Chunky Knit Blanco',           'precio':1250, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80&fit=crop&crop=bottom', 'categoria':'sueteres'},
        {'id':29, 'nombre':'Suéter Rayas Marino',          'precio':780,  'tallas':['XS','S','M','L','XL'], 'img':'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&q=80&fit=crop&crop=bottom', 'categoria':'sueteres'},
        {'id':30, 'nombre':'Cashmere Blend Nude',          'precio':1890, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=600&q=80&fit=crop&crop=bottom', 'categoria':'sueteres'},
        {'id':31, 'nombre':'Suéter Voluminoso Chocolate',  'precio':990,  'tallas':['XS','S','M','L'],       'img':'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&q=80&fit=crop&crop=top', 'categoria':'sueteres'},
        {'id':32, 'nombre':'Off-Shoulder Knit Crema',      'precio':860,  'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=600&q=80&fit=crop&crop=faces', 'categoria':'sueteres'},
        {'id':33, 'nombre':'Suéter Canalé Terracota',      'precio':710,  'tallas':['XS','S','M','L','XL'], 'img':'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80&fit=crop&crop=faces', 'categoria':'sueteres'},
        {'id':34, 'nombre':'Boxy Sweater Stone',           'precio':840,  'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=600&q=80&fit=crop&crop=faces', 'categoria':'sueteres'},
        {'id':35, 'nombre':'Suéter Con Botones Oliva',     'precio':930,  'tallas':['XS','S','M'],           'img':'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&q=80&fit=crop&crop=faces', 'categoria':'sueteres'},
        {'id':36, 'nombre':'Alpaca Blend Lavanda',         'precio':1450, 'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&q=80&fit=crop&crop=faces', 'categoria':'sueteres'},
        {'id':37, 'nombre':'Suéter Texturizado Arena',     'precio':780,  'tallas':['XS','S','M','L'],       'img':'https://images.unsplash.com/photo-1550614000-4895a10e1bfd?w=600&q=80&fit=crop&crop=faces', 'categoria':'sueteres'},
        {'id':38, 'nombre':'V-Neck Cashmere Negro',        'precio':2100, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80&fit=crop&crop=faces', 'categoria':'sueteres'},
        {'id':39, 'nombre':'Suéter Puff Sleeve Blanco',    'precio':890,  'tallas':['XS','S','M'],           'img':'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&q=80&fit=crop&crop=faces', 'categoria':'sueteres'},
        {'id':40, 'nombre':'Ribbed Turtleneck Gris',       'precio':760,  'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=600&q=80&fit=crop&crop=faces', 'categoria':'sueteres'},
    ],
    'chamarras': [
        {'id':41, 'nombre':'Puffer Jacket Negro',          'precio':1890, 'tallas':['XS','S','M','L','XL'], 'img':'https://images.unsplash.com/photo-1548624313-0396c75e4b1a?w=600&q=80&fit=crop', 'categoria':'chamarras'},
        {'id':42, 'nombre':'Leather Jacket Café',          'precio':4500, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=600&q=80&fit=crop', 'categoria':'chamarras'},
        {'id':43, 'nombre':'Puffer Beige Corto',           'precio':1650, 'tallas':['XS','S','M','L'],       'img':'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=600&q=80&fit=crop&crop=entropy', 'categoria':'chamarras'},
        {'id':44, 'nombre':'Bomber Varsity Gris',          'precio':1350, 'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80&fit=crop&crop=entropy', 'categoria':'chamarras'},
        {'id':45, 'nombre':'Shearling Jacket Caramel',     'precio':5200, 'tallas':['XS','S','M'],           'img':'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=600&q=80&fit=crop&crop=entropy', 'categoria':'chamarras'},
        {'id':46, 'nombre':'Denim Jacket Oversized',       'precio':980,  'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&q=80&fit=crop&crop=entropy', 'categoria':'chamarras'},
        {'id':47, 'nombre':'Moto Jacket Negro Mate',       'precio':3800, 'tallas':['XS','S','M','L'],       'img':'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&q=80&fit=crop&crop=entropy', 'categoria':'chamarras'},
        {'id':48, 'nombre':'Puffer Long Ivory',            'precio':2200, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1550614000-4895a10e1bfd?w=600&q=80&fit=crop&crop=entropy', 'categoria':'chamarras'},
        {'id':49, 'nombre':'Windbreaker Khaki',            'precio':1100, 'tallas':['XS','S','M','L','XL'], 'img':'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80&fit=crop&crop=entropy', 'categoria':'chamarras'},
        {'id':50, 'nombre':'Faux Fur Jacket Blanco',       'precio':2950, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&q=80&fit=crop&crop=entropy', 'categoria':'chamarras'},
        {'id':51, 'nombre':'Quilted Jacket Oliva',         'precio':1750, 'tallas':['XS','S','M','L'],       'img':'https://images.unsplash.com/photo-1548624313-0396c75e4b1a?w=600&q=80&fit=crop&crop=top', 'categoria':'chamarras'},
        {'id':52, 'nombre':'Suede Jacket Camel',           'precio':3400, 'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=600&q=80&fit=crop&crop=top', 'categoria':'chamarras'},
        {'id':53, 'nombre':'Puffer Pastel Lila',           'precio':1580, 'tallas':['XS','S','M'],           'img':'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=600&q=80&fit=crop&crop=center', 'categoria':'chamarras'},
        {'id':54, 'nombre':'Blazer Jacket Crema',          'precio':1900, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80&fit=crop&crop=center', 'categoria':'chamarras'},
        {'id':55, 'nombre':'Track Jacket Retro Negro',     'precio':1200, 'tallas':['XS','S','M','L','XL'], 'img':'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=600&q=80&fit=crop&crop=center', 'categoria':'chamarras'},
        {'id':56, 'nombre':'Sherpa Jacket Arena',          'precio':2100, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&q=80&fit=crop&crop=center', 'categoria':'chamarras'},
        {'id':57, 'nombre':'Crop Puffer Rosa Blush',       'precio':1490, 'tallas':['XS','S','M'],           'img':'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&q=80&fit=crop&crop=center', 'categoria':'chamarras'},
        {'id':58, 'nombre':'Varsity Jacket Chocolate',     'precio':1650, 'tallas':['S','M','L','XL'],       'img':'https://images.unsplash.com/photo-1550614000-4895a10e1bfd?w=600&q=80&fit=crop&crop=center', 'categoria':'chamarras'},
        {'id':59, 'nombre':'Reversible Puffer Gris/Negro', 'precio':2400, 'tallas':['XS','S','M','L'],       'img':'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80&fit=crop&crop=center', 'categoria':'chamarras'},
        {'id':60, 'nombre':'Parka Larga Kaki',             'precio':2800, 'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&q=80&fit=crop&crop=center', 'categoria':'chamarras'},
    ],
    'accesorios': [
        {'id':61, 'nombre':'Bufanda Lana Crema',           'precio':480,  'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=600&q=80&fit=crop', 'categoria':'accesorios'},
        {'id':62, 'nombre':'Beanie Trenzado Gris',         'precio':350,  'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&q=80&fit=crop&crop=top', 'categoria':'accesorios'},
        {'id':63, 'nombre':'Guantes Cuero Negro',          'precio':620,  'tallas':['S','M','L'],            'img':'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':64, 'nombre':'Bolso Bucket Camel',           'precio':1850, 'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1548624313-0396c75e4b1a?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':65, 'nombre':'Cinturón Piel Marrón',         'precio':780,  'tallas':['XS','S','M','L'],       'img':'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':66, 'nombre':'Sombrero Fieltro Camel',       'precio':690,  'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':67, 'nombre':'Bolso Tote Lona Beige',        'precio':950,  'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':68, 'nombre':'Calcetas Altas Lana',          'precio':220,  'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':69, 'nombre':'Echarpe Cachemira Gris',       'precio':1200, 'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':70, 'nombre':'Mochila Cuero Chocolate',      'precio':2100, 'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':71, 'nombre':'Collar Perlas Moderno',        'precio':540,  'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1550614000-4895a10e1bfd?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':72, 'nombre':'Aretes Dorados Minimalistas',  'precio':380,  'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':73, 'nombre':'Bolso Clutch Satín Negro',     'precio':1100, 'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':74, 'nombre':'Pañuelo Seda Estampado',       'precio':450,  'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':75, 'nombre':'Botas Chelsea Camel',          'precio':2800, 'tallas':['35','36','37','38','39','40'], 'img':'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&q=80&fit=crop&crop=right', 'categoria':'accesorios'},
        {'id':76, 'nombre':'Botas Altas Negras',           'precio':3200, 'tallas':['35','36','37','38','39'], 'img':'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=600&q=80&fit=crop&crop=left', 'categoria':'accesorios'},
        {'id':77, 'nombre':'Gorro Pompón Blanco',          'precio':290,  'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1548624313-0396c75e4b1a?w=600&q=80&fit=crop&crop=left', 'categoria':'accesorios'},
        {'id':78, 'nombre':'Guantes Tejidos Beige',        'precio':310,  'tallas':['S/M','L/XL'],           'img':'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=600&q=80&fit=crop&crop=left', 'categoria':'accesorios'},
        {'id':79, 'nombre':'Cinturón Cadena Dorado',       'precio':580,  'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=600&q=80&fit=crop&crop=left', 'categoria':'accesorios'},
        {'id':80, 'nombre':'Mini Bag Tejida Crema',        'precio':890,  'tallas':['Única'],                'img':'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80&fit=crop&crop=left', 'categoria':'accesorios'},
    ],
}

# Todos los productos en lista plana
TODOS = [p for cat in PRODUCTOS.values() for p in cat]

def get_producto(pid):
    return next((p for p in TODOS if p['id'] == pid), None)

def gen_folio():
    return 'NT-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ── RUTAS ────────────────────────────────────────────────────

@app.route('/', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('inicio'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        if not username or not password:
            error = 'Completa todos los campos'
        else:
            u = Usuario.query.filter_by(username=username).first()
            if u and u.check_password(password):
                login_user(u, remember=True)
                return redirect(url_for('inicio'))
            else:
                error = 'Usuario o contraseña incorrectos'
    return render_template('login.html', error=error)

@app.route('/registro', methods=['GET','POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('inicio'))
    error = None
    if request.method == 'POST':
        nombre   = request.form.get('nombre','').strip()
        apellido = request.form.get('apellido','').strip()
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        telefono = request.form.get('telefono','').strip()
        if not all([nombre, apellido, username, password, telefono]):
            error = 'Todos los campos son obligatorios'
        elif len(username) < 4:
            error = 'El usuario debe tener al menos 4 caracteres'
        elif len(password) < 6:
            error = 'La contraseña debe tener al menos 6 caracteres'
        elif not re.match(r'^\+?[\d\s\-]{7,15}$', telefono):
            error = 'Número de teléfono inválido'
        elif Usuario.query.filter_by(username=username).first():
            error = 'Ese nombre de usuario ya está en uso'
        else:
            u = Usuario(nombre=nombre, apellido=apellido, username=username, telefono=telefono)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('registro.html', error=error)

@app.route('/inicio')
@login_required
def inicio():
    destacados = TODOS[:8]
    return render_template('index.html', usuario=current_user, destacados=destacados, productos=PRODUCTOS)

@app.route('/catalogo')
@login_required
def catalogo():
    categoria = request.args.get('cat', 'todos')
    buscar    = request.args.get('q', '').lower()
    if categoria == 'todos':
        prods = TODOS
    else:
        prods = PRODUCTOS.get(categoria, [])
    if buscar:
        prods = [p for p in prods if buscar in p['nombre'].lower()]
    return render_template('catalogo.html', usuario=current_user, productos=prods, categoria=categoria, buscar=buscar)

@app.route('/producto/<int:pid>')
@login_required
def producto(pid):
    p = get_producto(pid)
    if not p:
        return redirect(url_for('catalogo'))
    relacionados = [x for x in PRODUCTOS.get(p['categoria'],[]) if x['id'] != pid][:4]
    return render_template('producto.html', usuario=current_user, producto=p, relacionados=relacionados)

# ── CARRITO (en session) ─────────────────────────────────────

@app.route('/carrito')
@login_required
def carrito():
    cart = session.get('carrito', {})
    items = []
    total = 0
    for key, item in cart.items():
        p = get_producto(item['id'])
        if p:
            subtotal = p['precio'] * item['qty']
            total += subtotal
            items.append({**p, 'qty': item['qty'], 'talla': item['talla'], 'key': key, 'subtotal': subtotal})
    return render_template('carrito.html', usuario=current_user, items=items, total=total)

@app.route('/carrito/agregar', methods=['POST'])
@login_required
def agregar_carrito():
    pid   = int(request.form.get('pid'))
    talla = request.form.get('talla','M')
    qty   = int(request.form.get('qty', 1))
    p     = get_producto(pid)
    if not p:
        return jsonify({'ok': False})
    cart = session.get('carrito', {})
    key  = f"{pid}_{talla}"
    if key in cart:
        cart[key]['qty'] += qty
    else:
        cart[key] = {'id': pid, 'talla': talla, 'qty': qty}
    session['carrito'] = cart
    session.modified   = True
    total_items = sum(i['qty'] for i in cart.values())
    return jsonify({'ok': True, 'total_items': total_items})

@app.route('/carrito/actualizar', methods=['POST'])
@login_required
def actualizar_carrito():
    key    = request.form.get('key')
    action = request.form.get('action')
    cart   = session.get('carrito', {})
    if key in cart:
        if action == 'add':
            cart[key]['qty'] += 1
        elif action == 'remove':
            cart[key]['qty'] -= 1
            if cart[key]['qty'] <= 0:
                del cart[key]
        elif action == 'delete':
            del cart[key]
    session['carrito'] = cart
    session.modified   = True
    return redirect(url_for('carrito'))

@app.route('/comprar', methods=['POST'])
@login_required
def comprar():
    keys = request.form.getlist('keys')
    cart = session.get('carrito', {})
    items_compra = []
    total = 0
    if not keys:  # comprar todo el carrito
        keys = list(cart.keys())
    for key in keys:
        if key in cart:
            item = cart[key]
            p    = get_producto(item['id'])
            if p:
                subtotal = p['precio'] * item['qty']
                total   += subtotal
                items_compra.append({
                    'nombre': p['nombre'], 'talla': item['talla'],
                    'qty': item['qty'], 'precio': p['precio'], 'subtotal': subtotal
                })
    if not items_compra:
        return redirect(url_for('carrito'))

    folio  = gen_folio()
    pedido = Pedido(
        usuario_id = current_user.id,
        folio      = folio,
        total      = total,
        items_json = json.dumps(items_compra)
    )
    db.session.add(pedido)
    db.session.commit()

    # Eliminar del carrito los items comprados
    for key in keys:
        cart.pop(key, None)
    session['carrito'] = cart
    session.modified   = True

    return redirect(url_for('ticket', folio=folio))

@app.route('/ticket/<folio>')
@login_required
def ticket(folio):
    pedido = Pedido.query.filter_by(folio=folio, usuario_id=current_user.id).first()
    if not pedido:
        return redirect(url_for('inicio'))
    items = json.loads(pedido.items_json)
    return render_template('ticket.html', usuario=current_user, pedido=pedido, items=items)

@app.route('/perfil')
@login_required
def perfil():
    pedidos = Pedido.query.filter_by(usuario_id=current_user.id).order_by(Pedido.creado_en.desc()).all()
    pedidos_data = []
    for p in pedidos:
        pedidos_data.append({**p.__dict__, 'items': json.loads(p.items_json)})
    return render_template('perfil.html', usuario=current_user, pedidos=pedidos_data)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# API: conteo carrito
@app.route('/api/carrito/count')
@login_required
def cart_count():
    cart = session.get('carrito', {})
    return jsonify({'count': sum(i['qty'] for i in cart.values())})

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
