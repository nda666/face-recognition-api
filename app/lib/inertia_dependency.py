from fastapi import Depends
from typing import Annotated
from inertia import InertiaConfig, inertia_dependency_factory, Inertia

inertia_config = InertiaConfig(
        # Your desired configuration
    )

inertia_dependency = inertia_dependency_factory(
    inertia_config
)

InertiaDependency = Annotated[Inertia, Depends(inertia_dependency)]