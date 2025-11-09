#!/bin/bash
echo "Validating architecture boundaries..."

# Check for domain layer dependencies on infrastructure
domain_deps=$(grep -r "import infrastructure" domain/ | grep -v "__init__.py" | wc -l)
if [ "$domain_deps" -gt 0 ]; then
    echo "ERROR: Domain layer depends on infrastructure ($domain_deps occurrences)"
    grep -r "import infrastructure" domain/ | grep -v "__init__.py"
    exit 1
fi

# Check for application layer dependencies on infrastructure
app_deps=$(grep -r "import infrastructure" application/ | grep -v "__init__.py" | wc -l)
if [ "$app_deps" -gt 0 ]; then
    echo "ERROR: Application layer depends on infrastructure ($app_deps occurrences)"
    grep -r "import infrastructure" application/ | grep -v "__init__.py"
    exit 1
fi

# Check for direct dependencies on infrastructure adapters in services
service_deps=$(grep -r "from infrastructure.adapters" services/ | grep -v "__init__.py" | wc -l)
if [ "$service_deps" -gt 0 ]; then
    echo "ERROR: Services layer has direct dependencies on infrastructure adapters ($service_deps occurrences)"
    grep -r "from infrastructure.adapters" services/ | grep -v "__init__.py"
    exit 1
fi

echo "Architecture validation passed!"
exit 0
