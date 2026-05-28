from db import Database
from normalizer import detectar_categoria, limpiar

def renormalizar_categorias_db():
    db = Database()
    
    # Obtener todos los productos
    productos = db.conn.execute("SELECT id, nombre_normalizado, categoria FROM productos").fetchall()
    
    print(f"Total de productos a revisar: {len(productos)}")
    
    for p in productos:
        nueva_categoria = detectar_categoria(p["nombre_normalizado"])

        if nueva_categoria != p['categoria']:
        
            # Actualizar si la categoría es distinta a la actual
            db.conn.execute(
                "UPDATE productos SET categoria = ? WHERE id = ?",
                (nueva_categoria, p["id"])
            )
            print(f"Nueva categoria para {p["nombre_normalizado"]} categeoria={nueva_categoria}")
    
            db.conn.commit()
    print("Re-normalización de categorías completada.")

if __name__ == "__main__":
    renormalizar_categorias_db()
