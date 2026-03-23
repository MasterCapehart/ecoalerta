import * as mobilenet from '@tensorflow-models/mobilenet'
import '@tensorflow/tfjs'

// Mapeo simple de keywords (inglés) a IDs de categorías y nombres en español
// Ajustar IDs según la base de datos real
const CATEGORY_MAPPINGS = [
    {
        keywords: ['trash', 'garbage', 'bin', 'waste'],
        categoryId: 1, // ID estimado para Domiciliarios
        categoryName: 'Residuos Domiciliarios',
        confidence: 0
    },
    {
        keywords: ['plastic', 'bottle', 'paper', 'cardboard', 'glass', 'can'],
        categoryId: 2, // ID estimado para Reciclables
        categoryName: 'Residuos Reciclables',
        confidence: 0
    },
    {
        keywords: ['couch', 'sofa', 'chair', 'table', 'wardrobe', 'furniture', 'bed', 'mattress'],
        categoryId: 3, // ID estimado para Voluminosos
        categoryName: 'Residuos Voluminosos',
        confidence: 0
    },
    {
        keywords: ['monitor', 'screen', 'television', 'laptop', 'computer', 'keyboard', 'mouse', 'phone', 'electronic'],
        categoryId: 4, // ID estimado para Electrónicos
        categoryName: 'Residuos Electrónicos',
        confidence: 0
    },
    {
        keywords: ['battery', 'chemical', 'paint', 'oil', 'gas', 'toxic'],
        categoryId: 5, // ID estimado para Peligrosos
        categoryName: 'Residuos Peligrosos',
        confidence: 0
    },
    {
        keywords: ['food', 'fruit', 'vegetable', 'meat', 'bread', 'organic', 'banana', 'apple', 'leftovers'],
        categoryId: 6, // Nuevo ID para Orgánicos
        categoryName: 'Residuos Orgánicos / Comida',
        confidence: 0
    },
    {
        keywords: ['brick', 'concrete', 'stone', 'wood', 'construction', 'rubble', 'tile', 'cement'],
        categoryId: 2, // Se puede mapear a Escombros (ID 2 en el form suele ser reciclable/escombro)
        categoryName: 'Escombros / Construcción',
        confidence: 0
    },
    {
        keywords: ['clothes', 'fabric', 'textile', 'shoe', 'shirt', 'pants', 'towel'],
        categoryId: 3, // Se puede mapear a Voluminosos/Otros
        categoryName: 'Ropa y Textiles',
        confidence: 0
    }
]

class AIService {
    constructor() {
        this.model = null
        this.isLoading = false
    }

    async loadModel() {
        if (this.model) return this.model
        if (this.isLoading) {
            // Esperar si ya está cargando
            return new Promise(resolve => {
                const check = setInterval(() => {
                    if (this.model) {
                        clearInterval(check)
                        resolve(this.model)
                    }
                }, 100)
            })
        }

        try {
            this.isLoading = true
            console.log('Cargando modelo MobileNet...')
            this.model = await mobilenet.load({ version: 2, alpha: 0.5 }) // Versión ligera
            this.isLoading = false
            console.log('Modelo cargado.')
            return this.model
        } catch (error) {
            console.error('Error cargando modelo AI:', error)
            this.isLoading = false
            return null
        }
    }

    async classifyImage(imageElement) {
        const model = await this.loadModel()
        if (!model) return null

        try {
            // Clasificar
            const predictions = await model.classify(imageElement)
            console.log('Predicciones AI:', predictions)

            // Procesar predicciones para encontrar coincidencias
            let bestMatch = null
            let maxScore = 0

            for (const pred of predictions) {
                const className = pred.className.toLowerCase()
                const probability = pred.probability

                // Buscar keyword
                for (const mapping of CATEGORY_MAPPINGS) {
                    const match = mapping.keywords.some(k => className.includes(k))
                    if (match && probability > maxScore) {
                        bestMatch = mapping
                        maxScore = probability
                    }
                }
            }

            if (bestMatch && maxScore > 0.05) { // Bajamos un poco el umbral para captar más detalles
                return {
                    ...bestMatch,
                    originalPrediction: predictions[0].className,
                    detectedProduct: predictions[0].className.split(',')[0], // Tomar el primer término
                    score: maxScore
                }
            }

            return null
        } catch (error) {
            console.error('Error clasificando imagen:', error)
            return null
        }
    }
}

export default new AIService()
