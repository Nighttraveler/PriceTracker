from db import Database
from datetime import timedelta

def corregir_timestamps():
    db = Database()
    
    # Obtener todas las variantes que tienen múltiples precios con la misma fecha
    # Agrupamos por variante_id para ordenar sus precios por id (que es auto-incremental y marca el orden de inserción)
    variantes = db.conn.execute("SELECT DISTINCT variante_id FROM precios").fetchall()
    
    for v in variantes:
        variante_id = v["variante_id"]
        # Obtener precios para esta variante ordenados por ID (más antiguo primero)
        precios = db.conn.execute(
            "SELECT id, fecha FROM precios WHERE variante_id = ? ORDER BY id ASC", 
            (variante_id,)
        ).fetchall()
        
        # Iterar y ajustar los segundos para que los más antiguos queden antes
        # Tomamos el tiempo base del primero y restamos segundos para los anteriores
        # O mejor: incrementamos segundos para los más nuevos respecto al primero
        base_time = None
        for i, p in enumerate(precios):
            if i == 0:
                base_time = datetime.strptime(p["fecha"], "%Y-%m-%d %H:%M:%S")
                continue
            
            # Ajustar timestamp incrementando 1 segundo por cada entrada nueva
            new_time = base_time + timedelta(seconds=i)
            db.conn.execute(
                "UPDATE precios SET fecha = ? WHERE id = ?",
                (new_time.strftime("%Y-%m-%d %H:%M:%S"), p["id"])
            )
            
    db.conn.commit()
    print("Corrección de timestamps basada en orden de inserción completada.")

if __name__ == "__main__":
    from datetime import datetime
    corregir_timestamps()
