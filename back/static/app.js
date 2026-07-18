const formulario = document.querySelector(".formulario");

formulario.addEventListener("submit", function (e) {
    e.preventDefault();

    const datos = {
        nombre: document.getElementById("nombre").value,
        edad: Number(document.getElementById("edad").value),
        genero: document.getElementById("genero").value,
        destino: document.getElementById("destino").value,
        fecha: document.getElementById("fecha").value,
        presupuesto: Number(document.getElementById("presupuesto").value)
    };

    console.log("Datos enviados");
    console.log(datos);


    fetch("/cotizar", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(datos)
    })
        .then(res => res.json())
        .then(data => {
            console.log(data);
            if (data.error) {
                mostrarError(data.error);
                return;
            }

            mostrarTabla(data);
            mostrarMapa(data);
            mostrarGraficaDispersion(data);
        })
        .catch(error => {
            console.error(error);
        })
});


function mostrarTabla(data) {
    const tablaRespuestas = document.getElementById("tabla_respuestas");
    const precioDisponible =
        data.precio_estimado !== null && data.precio_estimado !== undefined && !Number.isNaN(Number(data.precio_estimado));

    let resultadoViabilidad
    if (data.es_viable === true) {
        resultadoViabilidad = "Si"
    } else if (data.es_viable === false) {
        resultadoViabilidad = "No"
    } else {
        resultadoViabilidad = "No se puede determinar"
    }


    tablaRespuestas.innerHTML = `
        <table>
            <tr>
                <th>Nombre</th>
                <td>${data.nombre}</td>
            </tr>

            <tr>
                <th>Edad</th>
                <td>${data.edad}</td>
            </tr>

            <tr>
                <th>Destino</th>
                <td>
                    ${data.destino.tipo === "ciudad"
            ? `${data.destino.ciudad}, ${data.destino.pais}`
            : data.destino.pais
        }
                </td>
            </tr>

            <tr>
                <th>Visa Requerida</th>
                <td>${data.visa}</td>
            </tr>

            <tr>
                <th>ISO3</th>
                <td>${data.destino.ISO3}</td>
            </tr>

            <tr>
                <th>Fecha</th>
                <td>${data.fecha}</td>
            </tr>

            <tr>
                <th>Presupuesto</th>
                <td>
                    ${Number(data.presupuesto).toLocaleString(
            "es-MX",
            {
                style: "currency",
                currency: "MXN"
            }
        )}
                </td>
            </tr>
            
            <tr>
    <th>Precio estimado del vuelo</th>
    <td>
        ${data.precio_estimado !== null
            ? Number(data.precio_estimado).toLocaleString("es-MX", {
                style: "currency",
                currency: "MXN"
            })
            : "Escribe una ciudad para conocer el precio del vuelo"
        }
    </td>
    <tr>
        <th>¿Es viable?</th>
        <td>${resultadoViabilidad}</td>
    </tr>
</tr>

        </table>
    `;
}

function mostrarError(mensaje) {
    const tablaRespuestas = document.getElementById("tabla_respuestas");
    tablaRespuestas.innerHTML = `<p class="mensaje-error">${mensaje}</p>`
}

function mostrarMapa(data) {

    const contenedor =
        document.getElementById("grafica_mapa");

    const datos = data.datos_graficas;

    if (!datos || datos.length === 0) {
        Plotly.purge(contenedor);

        contenedor.innerHTML = `
            <p>No hay datos disponibles para generar el mapa.</p>
        `;

        return;
    }

    const categorias = [
        "Otros Destinos",
        "Top 5 Más Seguros y Económicos",
        `Tu Destino (${data.pais})`
    ];

    const colores = {
        "Otros Destinos": "lightgrey",
        "Top 5 Más Seguros y Económicos": "green",
        [`Tu Destino (${data.pais})`]: "orange"
    };

    const trazas = categorias.map(categoria => {

        const registros = datos.filter(
            item => item.categoria === categoria
        );

        return {
            type: "choropleth",
            locationmode: "ISO-3",
            locations: registros.map(
                item => item.iso3
            ),
            z: registros.map(() => 1),
            text: registros.map(
                item => item.pais
            ),
            customdata: registros.map(item => [
                item.indice_seguridad,
                item.indice_costo_vida
            ]),
            hovertemplate:
                "<b>%{text}</b><br>" +
                "Índice de seguridad: %{customdata[0]}<br>" +
                "Índice de costo de vida: %{customdata[1]}" +
                "<extra></extra>",
            name: categoria,
            showscale: false,
            colorscale: [
                [0, colores[categoria]],
                [1, colores[categoria]]
            ],
            zmin: 0,
            zmax: 1
        };
    });

    const diseño = {
        title: {
            text:
                `Mapa de alternativas: ${data.pais} ` +
                "vs. opciones seguras y económicas"
        },
        geo: {
            projection: {
                type: "natural earth"
            },
            showcoastlines: true,
            coastlinecolor: "white",
            showland: true,
            landcolor: "white",
            showocean: true,
            oceancolor: "aliceblue"
        },
        legend: {
            title: {
                text: "Categorías de viaje"
            }
        },
        margin: {
            r: 0,
            t: 60,
            l: 0,
            b: 0
        }
    };

    Plotly.newPlot(
        contenedor,
        trazas,
        diseño,
        {
            responsive: true,
            displaylogo: false
        }
    );
}

function mostrarGraficaDispersion(data) {

    const contenedor =
        document.getElementById("grafica_dispersion");

    const datos = data.datos_graficas;

    if (!datos || datos.length === 0) {
        Plotly.purge(contenedor);

        contenedor.innerHTML = `
            <p>No hay datos disponibles para generar la gráfica.</p>
        `;

        return;
    }

    const categoriaDestino =
        `Tu Destino (${data.pais})`;

    const configuracionCategorias = [
        {
            nombre: "Otros Destinos",
            tamaño: 7,
            simbolo: "circle",
            opacidad: 0.5,
            color: "grey"
        },
        {
            nombre: "Top 5 Más Seguros y Económicos",
            tamaño: 12,
            simbolo: "circle",
            opacidad: 1,
            color: "green"
        },
        {
            nombre: categoriaDestino,
            tamaño: 30,
            simbolo: "star",
            opacidad: 1,
            color: "orange"
        }
    ];

    const trazas = configuracionCategorias.map(configuracion => {

        const registros = datos.filter(
            item =>
                item.categoria === configuracion.nombre
        );

        return {
            type: "scatter",
            mode: "markers",
            name: configuracion.nombre,

            x: registros.map(
                item => item.indice_costo_vida
            ),

            y: registros.map(
                item => item.indice_seguridad
            ),

            text: registros.map(
                item => item.pais
            ),

            marker: {
                size: configuracion.tamaño,
                symbol: configuracion.simbolo,
                opacity: configuracion.opacidad,
                color: configuracion.color
            },

            hovertemplate:
                "<b>%{text}</b><br>" +
                "Costo de vida: %{x}<br>" +
                "Seguridad: %{y}" +
                "<extra></extra>"
        };
    });

    const diseño = {
        title: {
            text:
                `Análisis interactivo: ${data.pais} ` +
                "vs. alternativas en seguridad y costo de vida"
        },

        xaxis: {
            title: {
                text:
                    "Índice de costo de vida " +
                    "(menor es más barato)"
            }
        },

        yaxis: {
            title: {
                text:
                    "Índice de seguridad " +
                    "(mayor es más seguro)"
            }
        },

        hovermode: "closest",

        legend: {
            title: {
                text: "Filtros de visualización"
            }
        },

        template: "plotly_white",

        margin: {
            t: 70,
            r: 30,
            b: 80,
            l: 80
        }
    };

    Plotly.newPlot(
        contenedor,
        trazas,
        diseño,
        {
            responsive: true,
            displaylogo: false
        }
    );
}

