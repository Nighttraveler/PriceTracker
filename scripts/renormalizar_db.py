from db import Database
from normalizer import Normalizer

def re_normalizar_db():
    db = Database()
    norm = Normalizer(db)
    
    # Obtener todas las variantes existentes
    variantes = db.conn.execute("SELECT id, nombre_original, fuente_id, producto_id FROM variantes").fetchall()
    
    print(f"Total de variantes a procesar: {len(variantes)}")
    
    for v in variantes:
        # Re-normalizar el nombre original
        # Esto usará la lógica actualizada de obtener_o_crear_producto
        nuevo_producto_id = norm.obtener_o_crear_producto(v["nombre_original"], v["fuente_id"])
        
        # Si el producto_id cambió, actualizar la variante
        if nuevo_producto_id != v["producto_id"]:
            print(f"Actualizando variante '{v['nombre_original']}': {v['producto_id']} -> {nuevo_producto_id}")
            db.conn.execute(
                "UPDATE variantes SET producto_id = ? WHERE id = ?",
                (nuevo_producto_id, v["id"])
            )
    
    db.conn.commit()
    print("Re-normalización completada.")

if __name__ == "__main__":
    re_normalizar_db()
