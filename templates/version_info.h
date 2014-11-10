// Copyright 20** MakerBot Industries

#ifndef {{project}}_VERSION_INFO_H
#define {{project}}_VERSION_INFO_H

#include <string>

#include "mbcoreutils/version.h"

namespace {{namespace}} {

static const MakerBot::Version version = MakerBot::Version(
    {{major}},
    {{minor}},
    {{point}},
    {{build}});

static const std::string commitHash("{{hash}}");
static const bool modified({{modified}});

}  // namespace {{namespace}}

#endif  // {{project}}_VERSION_INFO_H
