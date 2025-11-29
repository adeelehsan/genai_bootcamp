"""
Anime Recommender Flask Application
Simple and clean implementation with Prometheus metrics
"""

from flask import render_template, Flask, request, Response, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from pipeline.pipline import AnimeRecommendationPipeline
from dotenv import load_dotenv
import time
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Latency',
    ['method', 'endpoint']
)

RECOMMENDATION_COUNT = Counter(
    'recommendations_total',
    'Total Recommendations Generated',
    ['status']
)

RECOMMENDATION_LATENCY = Histogram(
    'recommendation_duration_seconds',
    'Recommendation Generation Latency'
)

ACTIVE_REQUESTS = Gauge(
    'active_requests',
    'Number of Active Requests'
)

PIPELINE_STATUS = Gauge(
    'pipeline_status',
    'Pipeline Health Status (1=healthy, 0=unhealthy)'
)


def create_app():
    """Create and configure Flask application"""

    app = Flask(__name__)

    # Initialize pipeline
    logger.info("🚀 Initializing Anime Recommendation Pipeline...")
    try:
        pipeline = AnimeRecommendationPipeline(persist_dir="chroma_db")
        PIPELINE_STATUS.set(1)  # Healthy
        logger.info("✅ Pipeline initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize pipeline: {str(e)}")
        pipeline = None
        PIPELINE_STATUS.set(0)  # Unhealthy

    @app.route("/")
    def index():
        """Main page"""
        REQUEST_COUNT.labels(method='GET', endpoint='/', status='200').inc()
        return render_template("index.html")

    @app.route("/get", methods=["POST"])
    def get_response():
        """Get anime recommendation"""
        ACTIVE_REQUESTS.inc()
        start_time = time.time()

        try:
            # Get user input
            user_input = request.form.get("msg", "").strip()

            if not user_input:
                REQUEST_COUNT.labels(method='POST', endpoint='/get', status='400').inc()
                RECOMMENDATION_COUNT.labels(status='error').inc()
                return "Please provide a query", 400

            if pipeline is None:
                REQUEST_COUNT.labels(method='POST', endpoint='/get', status='503').inc()
                RECOMMENDATION_COUNT.labels(status='error').inc()
                return "Recommendation system is not available", 503

            # Get recommendation
            logger.info(f"📝 Processing query: {user_input[:50]}...")

            with RECOMMENDATION_LATENCY.time():
                response = pipeline.get_recommendation(user_input)

            # Record metrics
            duration = time.time() - start_time
            REQUEST_COUNT.labels(method='POST', endpoint='/get', status='200').inc()
            REQUEST_LATENCY.labels(method='POST', endpoint='/get').observe(duration)
            RECOMMENDATION_COUNT.labels(status='success').inc()

            logger.info(f"✅ Recommendation generated in {duration:.2f}s")

            return response

        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            REQUEST_COUNT.labels(method='POST', endpoint='/get', status='500').inc()
            RECOMMENDATION_COUNT.labels(status='error').inc()
            return f"An error occurred: {str(e)}", 500

        finally:
            ACTIVE_REQUESTS.dec()

    @app.route("/api/recommend", methods=["POST"])
    def api_recommend():
        """API endpoint for recommendations (JSON)"""
        ACTIVE_REQUESTS.inc()
        start_time = time.time()

        try:
            # Get JSON data
            data = request.get_json()
            if not data or 'query' not in data:
                REQUEST_COUNT.labels(method='POST', endpoint='/api/recommend', status='400').inc()
                return jsonify({"error": "Missing 'query' field"}), 400

            user_input = data['query'].strip()

            if not user_input:
                REQUEST_COUNT.labels(method='POST', endpoint='/api/recommend', status='400').inc()
                return jsonify({"error": "Query cannot be empty"}), 400

            if pipeline is None:
                REQUEST_COUNT.labels(method='POST', endpoint='/api/recommend', status='503').inc()
                return jsonify({"error": "Recommendation system not available"}), 503

            # Get recommendation
            logger.info(f"📝 API query: {user_input[:50]}...")

            with RECOMMENDATION_LATENCY.time():
                response = pipeline.get_recommendation(user_input)

            # Record metrics
            duration = time.time() - start_time
            REQUEST_COUNT.labels(method='POST', endpoint='/api/recommend', status='200').inc()
            REQUEST_LATENCY.labels(method='POST', endpoint='/api/recommend').observe(duration)
            RECOMMENDATION_COUNT.labels(status='success').inc()

            logger.info(f"✅ API recommendation generated in {duration:.2f}s")

            return jsonify({
                "success": True,
                "recommendation": response,
                "query": user_input,
                "duration": round(duration, 2)
            })

        except Exception as e:
            logger.error(f"❌ API Error: {str(e)}")
            REQUEST_COUNT.labels(method='POST', endpoint='/api/recommend', status='500').inc()
            RECOMMENDATION_COUNT.labels(status='error').inc()
            return jsonify({"error": str(e)}), 500

        finally:
            ACTIVE_REQUESTS.dec()

    @app.route("/health")
    def health():
        """Health check endpoint"""
        REQUEST_COUNT.labels(method='GET', endpoint='/health', status='200').inc()

        is_healthy = pipeline is not None
        status_code = 200 if is_healthy else 503

        return jsonify({
            "status": "healthy" if is_healthy else "unhealthy",
            "pipeline_initialized": is_healthy
        }), status_code

    @app.route("/metrics")
    def metrics():
        """Prometheus metrics endpoint"""
        return Response(generate_latest(), mimetype="text/plain")

    return app


if __name__ == "__main__":
    app = create_app()

    logger.info("=" * 60)
    logger.info("🎌 Anime Recommender Application")
    logger.info("=" * 60)
    logger.info("📍 Main UI:        http://localhost:8000/")
    logger.info("📊 Metrics:        http://localhost:8000/metrics")
    logger.info("🏥 Health Check:   http://localhost:8000/health")
    logger.info("🔗 API Endpoint:   http://localhost:8000/api/recommend")
    logger.info("=" * 60)
    logger.info("Press CTRL+C to quit\n")

    app.run(host="0.0.0.0", port=8000, debug=True)
