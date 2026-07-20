import pandas as pd
from database import engine
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

def cotizar_viaje(datos):

    destino = obtenerDestino(datos["destino"])

    if destino is None:
        return{
            "error":"No se encontro el pais o ciudad ingresada"
        }
    
    visa = revisionDeVisado(destino["id_pais"])
    datos_graficas = obtenerDataParaGraficas(destino["id_pais"])

    precio_estimado = None
    es_viable = None

    if destino["tipo"] == "ciudad":
        precio_estimado = predecirPrecio(
            destino["id_ciudad"],
            datos["fecha"]
        )
        if precio_estimado is not None:
            es_viable= (datos["presupuesto"] >= precio_estimado)

    return {
        "nombre": datos["nombre"],
        "edad": datos["edad"],
        "genero": datos["genero"],
        "destino": destino,
        "tipo_destino": destino["tipo"],
        "pais": destino["pais"],
        "visa": visa,
        "ISO3": destino["ISO3"],
        "ciudad": destino["ciudad"],
        "fecha": datos["fecha"],
        "presupuesto": datos["presupuesto"],
        "precio_estimado": precio_estimado,
        "es_viable": es_viable,
        "datos_graficas": datos_graficas
    }



def obtenerDestino(entrada):

    entrada = entrada.strip().title()

    # Buscar si la entrada es un país
    sql_pais = """
        SELECT
        id_pais,
        TRIM(nombre) AS nombre,
        TRIM(iso3) AS iso3
        FROM paises                                  
        WHERE TRIM(nombre) = %(entrada)s;
    """

    fila_pais = pd.read_sql(
        sql_pais,
        engine,
        params={"entrada": entrada}
    )

    # Si es un país
    if not fila_pais.empty:
        return {
            "tipo": "pais",
            "id_ciudad":None,
            "id_pais": int(fila_pais.iloc[0]["id_pais"]),
            "pais": fila_pais.iloc[0]["nombre"],
            "ISO3": fila_pais.iloc[0]["iso3"],
            "ciudad": None
        }

    # Buscar si la entrada es una ciudad
    sql_ciudad = """
        SELECT
        c.id_ciudad,
        p.id_pais,
        TRIM(c.nombre) AS ciudad,
        TRIM(p.nombre) AS pais,
        TRIM(p.iso3) AS iso3
        FROM ciudades c
        JOIN paises p
        ON c.id_pais = p.id_pais
    WHERE TRIM(c.nombre) = %(entrada)s;
    """

    fila_ciudad = pd.read_sql(
        sql_ciudad,
        engine,
        params={"entrada": entrada}
    )

    if not fila_ciudad.empty:
        return {
        "tipo": "ciudad",
        "id_ciudad": int(fila_ciudad.iloc[0]["id_ciudad"]),
        "id_pais": int(fila_ciudad.iloc[0]["id_pais"]),
        "pais": fila_ciudad.iloc[0]["pais"],
        "ISO3": fila_ciudad.iloc[0]["iso3"],
        "ciudad": fila_ciudad.iloc[0]["ciudad"]
        }

    return None




def revisionDeVisado(id_pais):
    sql = """
        SELECT TRIM(requisito) AS requisito
        FROM visados
        WHERE id_pais = %(id_pais)s
        """
    fila = pd.read_sql(
        sql,
        engine,
        params={"id_pais": id_pais}
    )

    if fila.empty:
        return "Informacion no disponnible"
    
    return fila.iloc[0]["requisito"]




def predecirPrecio(id_ciudad, fecha_viaje):
    sql = """
        SELECT fecha, precio_mxn
        FROM vuelos_historicos
        WHERE id_ciudad = %(id_ciudad)s
        ORDER BY fecha
        """
    vuelos = pd.read_sql(
        sql,
        engine,
        params={"id_ciudad": id_ciudad}
    )

    if vuelos.empty:
        return None
    
    vuelos["fecha"] = pd.to_datetime(vuelos["fecha"], errors="coerce")
    vuelos["precio_mxn"] = pd.to_numeric(vuelos["precio_mxn"], errors="coerce")

    vuelos = vuelos.dropna(subset=["fecha", "precio_mxn"])

    if vuelos.empty:
        return None

    fecha_viaje = pd.to_datetime(fecha_viaje, errors="coerce")

    if pd.isna(fecha_viaje):
        return None

    #fecha convertida a dias
    fecha_base = vuelos["fecha"].min()

    vuelos["dias"] = (
        vuelos["fecha"] - fecha_base
    ).dt.days

    dias_fecha_viaje = (
        fecha_viaje - fecha_base
    ).days

    X=vuelos[["dias"]]
    y=vuelos["precio_mxn"]

    X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
    )

    modelo = LinearRegression()
    modelo.fit(X_train, y_train)

    datos_prediccion = pd.DataFrame({
        "dias": [dias_fecha_viaje]
    })

    precio_estimado = modelo.predict(datos_prediccion)[0]

    return round(float(precio_estimado), 2)



def obtenerDataParaGraficas(id_pais):
    sql = """
        SELECT 
        p.id_pais, 
        TRIM(p.nombre) AS pais,
        TRIM(p.iso3) AS iso3,
        i.indice_seguridad,
        i.indice_costo_vida
        FROM indices i
        JOIN paises p
        ON i.id_pais = p.id_pais;
        """
    
    indices = pd.read_sql(sql, engine)

    if indices.empty:
        return None
    
    indices["indice_seguridad"] = pd.to_numeric(indices["indice_seguridad"], errors="coerce")
    indices["indice_costo_vida"] = pd.to_numeric(indices["indice_costo_vida"], errors="coerce")

    indices = indices.dropna(subset=["indice_seguridad", "indice_costo_vida"])

    pais_seleccionado = indices[indices["id_pais"] == id_pais].copy()
    if pais_seleccionado.empty:
        return None
    

    nombre_pais = pais_seleccionado.iloc[0]["pais"]


    otros_paises = indices[indices["id_pais"] != id_pais].copy()
    paises_seguros = otros_paises[otros_paises["indice_seguridad"] >= 65]

    top5_ideales = paises_seguros.nsmallest(5,  "indice_costo_vida")

    otros_paises["categoria"] = "Otros Destinos"

    otros_paises.loc[
        otros_paises["id_pais"].isin(top5_ideales["id_pais"]),
            "categoria"] = "Top 5 Más Seguros y Económicos"
    
    


    pais_seleccionado["categoria"] = (f'Tu Destino ({nombre_pais})')
    
    datos_graficas = pd.concat([otros_paises, pais_seleccionado], ignore_index= True)

    return datos_graficas[
        [
        "pais",
        "iso3",
        "indice_seguridad",
        "indice_costo_vida",
        "categoria"
        ]
    ].to_dict(orient="records")