"""
CoH1 × Mistral AI Mod - System Prompt Engine

Generates CoH1-specific system prompts with domain knowledge, hard rules,
and faction-specific strategies for the Mistral AI strategist.

Features:
- CoH1 domain knowledge encoding
- Faction-specific prompts (Allies/Axis)
- Hard rules (fuel cutoffs, counter-units matrix)
- Difficulty doctrine prompts
- JSON mode prompt formatting
- Dynamic prompt generation based on game state

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-11-21
"""

import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ============================================
# Enums
# ============================================

class Faction(Enum):
    """Game factions."""
    ALLIES = "allies"
    AXIS = "axis"


class Difficulty(Enum):
    """AI difficulty levels."""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXPERT = "expert"


class GamePhase(Enum):
    """Game phases."""
    EARLY = "early"
    MID = "mid"
    LATE = "late"


# ============================================
# Unit Counter Matrix
# ============================================

# Counter relationships: unit_type -> effective_against
COUNTER_UNITS = {
    # Infantry counters
    "riflemen": ["engineer", "scout_car"],
    "volks": ["engineer", "scout_car"],
    "grenadier": ["infantry", "engineer"],
    
    # Anti-tank counters
    "bazooka": ["light_tank", "medium_tank"],
    "panzerschreck": ["light_tank", "medium_tank"],
    
    # Anti-infantry counters
    "machine_gun": ["riflemen", "volks", "engineer"],
    "hmg": ["riflemen", "volks", "engineer"],
    
    # Tank counters
    "light_tank": ["scout_car", "machine_gun", "hmg"],
    "medium_tank": ["light_tank", "bazooka", "panzerschreck"],
    "heavy_tank": ["medium_tank", "bazooka", "panzerschreck"],
    
    # Support counters
    "mortar": ["infantry", "machine_gun", "hmg"],
    "sniper": ["machine_gun", "hmg", "mortar"],
}

# Unit types that are strong against each unit
UNIT_STRENGTHS = {
    "riflemen": {"strong_against": ["engineer"], "weak_against": ["machine_gun", "hmg", "tank"]},
    "volks": {"strong_against": ["engineer"], "weak_against": ["machine_gun", "hmg", "tank"]},
    "engineer": {"strong_against": [], "weak_against": ["riflemen", "volks", "grenadier"]},
    "scout_car": {"strong_against": ["infantry"], "weak_against": ["bazooka", "panzerschreck", "tank"]},
    "grenadier": {"strong_against": ["infantry", "building"], "weak_against": ["tank"]},
    "machine_gun": {"strong_against": ["infantry"], "weak_against": ["sniper", "mortar", "tank"]},
    "hmg": {"strong_against": ["infantry"], "weak_against": ["sniper", "mortar", "tank"]},
    "mortar": {"strong_against": ["infantry", "machine_gun"], "weak_against": ["sniper", "tank"]},
    "sniper": {"strong_against": ["machine_gun", "hmg"], "weak_against": ["infantry"]},
    "bazooka": {"strong_against": ["tank"], "weak_against": ["infantry", "scout_car"]},
    "panzerschreck": {"strong_against": ["tank"], "weak_against": ["infantry", "scout_car"]},
    "light_tank": {"strong_against": ["infantry", "scout_car", "machine_gun"], "weak_against": ["bazooka", "panzerschreck", "medium_tank"]},
    "medium_tank": {"strong_against": ["infantry", "light_tank", "scout_car"], "weak_against": ["bazooka", "panzerschreck", "heavy_tank"]},
    "heavy_tank": {"strong_against": ["infantry", "light_tank", "medium_tank"], "weak_against": ["bazooka", "panzerschreck"]},
}


# ============================================
# Resource Management Rules
# ============================================

# Fuel cutoffs for different actions
FUEL_CUTOFFS = {
    "build_tank": 200,      # Minimum fuel to build a tank
    "build_vehicle": 100,   # Minimum fuel to build a vehicle
    "produce_tank": 150,    # Minimum fuel to produce a tank
    "emergency": 50,        # Minimum fuel for emergency actions
}

# Manpower cutoffs
MANPOWER_CUTOFFS = {
    "build_infantry": 200,  # Minimum manpower to build infantry
    "produce_infantry": 150,
    "emergency": 100,
}

# Munitions cutoffs
MUNITIONS_CUTOFFS = {
    "use_ability": 50,      # Minimum munitions to use abilities
    "emergency": 20,
}


# ============================================
# Strategic Rules
# ============================================

# Priority order for actions
ACTION_PRIORITIES = {
    "retreat": 100,         # Highest priority - save units
    "defend": 90,           # Defend key positions
    "counter_attack": 80,   # Counter enemy pushes
    "capture_point": 70,    # Capture strategic points
    "build_economy": 60,    # Build resource structures
    "build_army": 50,       # Build military structures
    "produce_units": 40,   # Produce units
    "scout": 30,            # Scout enemy positions
    "expand": 20,           # Expand territory
}

# Building costs and requirements
BUILDING_COSTS = {
    "barracks": {"manpower": 200, "fuel": 0, "time": 60},
    "war_factory": {"manpower": 400, "fuel": 100, "time": 90},
    "tank_depot": {"manpower": 400, "fuel": 100, "time": 120},
    "command_post": {"manpower": 300, "fuel": 0, "time": 45},
    "observation_post": {"manpower": 100, "fuel": 0, "time": 30},
}

# Unit costs
UNIT_COSTS = {
    "riflemen": {"manpower": 180, "fuel": 0, "pop": 6},
    "engineer": {"manpower": 200, "fuel": 0, "pop": 5},
    "scout_car": {"manpower": 120, "fuel": 40, "pop": 4},
    "grenadier": {"manpower": 200, "fuel": 0, "munitions": 20, "pop": 6},
    "machine_gun": {"manpower": 200, "fuel": 0, "munitions": 40, "pop": 6},
    "mortar": {"manpower": 240, "fuel": 0, "munitions": 40, "pop": 6},
    "sniper": {"manpower": 250, "fuel": 0, "pop": 4},
    "bazooka": {"manpower": 220, "fuel": 0, "munitions": 20, "pop": 5},
    "light_tank": {"manpower": 480, "fuel": 120, "munitions": 60, "pop": 8},
    "medium_tank": {"manpower": 720, "fuel": 180, "munitions": 100, "pop": 10},
    "heavy_tank": {"manpower": 1000, "fuel": 250, "munitions": 150, "pop": 12},
}


# ============================================
# Prompt Templates
# ============================================

# Base system prompt template
BASE_SYSTEM_PROMPT = """
You are the AI Strategist for Company of Heroes 1 (CoH1). Your role is to make high-level strategic decisions 
for the AI player. You will receive game state information and must respond with JSON-formatted strategic intents.

## Core Principles:
1. NEVER make illegal or impossible commands - always consider resource costs and game rules
2. Think like a skilled CoH1 player - balance economy, army composition, and map control
3. Adapt to the current game phase (early, mid, late)
4. Respond to enemy actions and threats
5. Maintain resource flow and production queues

## Response Format:
You MUST respond with a JSON object containing an array of "intentions". Each intention must have:
- "intent": string (one of: BUILD, TECH, PRODUCE, ATTACK, DEFEND, RETREAT, CAPTURE, EXPAND, REINFORCE, FALLBACK)
- "confidence": number (0.0 to 1.0)
- "reasoning": string (brief explanation)
- "priority": number (1-10, higher = more urgent)
- Additional fields based on intent type

## Intent Types and Required Fields:
- BUILD: building_type (string), position (array [x, y, z]), engineer_id (number or null)
- TECH: tech_name (string), building_id (number or null)
- PRODUCE: unit_type (string), building_id (number), count (number, default 1)
- ATTACK: target_position (array [x, y, z]), units (array of squad_ids)
- DEFEND: position (array [x, y, z]), units (array of squad_ids)
- RETREAT: squad_id (number), position (array [x, y, z] or null)
- CAPTURE: squad_id (number), point_id (number)
- EXPAND: direction (string), squad_id (number or null)
- REINFORCE: position (array [x, y, z]), squad_ids (array)
- FALLBACK: position (array [x, y, z])

## Important Rules:
- Always check resource availability before suggesting actions
- Consider population cap (max 100 for most maps)
- Fuel is critical for vehicles - don't build tanks without fuel
- Infantry are versatile but vulnerable to tanks
- Always maintain at least one engineer for repairs
- Capture points provide resources - prioritize controlling them
- Retreat units at low health (below 30%) to save them
- Use cover and terrain to your advantage

## Game Knowledge:
{game_knowledge}

## Current Game Context:
{context}

## Your Task:
Analyze the current game state and provide strategic intents. Think step-by-step and justify your decisions.
"""


# Faction-specific knowledge
FACTION_KNOWLEDGE = {
    Faction.ALLIES: {
        "name": "Allies",
        "strengths": [
            "Strong early-game infantry (Riflemen are cost-effective)",
            "Good anti-tank options (Bazooka teams)",
            "Versatile engineer units",
            "Strong defensive structures"
        ],
        "weaknesses": [
            "Tanks are more expensive than Axis equivalents",
            "Fewer specialized infantry options",
            "Slower tank production"
        ],
        "recommended_openers": [
            "Riflemen + Engineer rush for early map control",
            "Barracks first for infantry focus",
            "War Factory for vehicle production"
        ],
        "counter_strategy": "Use Bazookas against Axis tanks, focus on controlling capture points"
    },
    Faction.AXIS: {
        "name": "Axis",
        "strengths": [
            "Cheaper infantry (Volksgrenadiers)",
            "More specialized infantry options",
            "Faster tank production",
            "Strong early-game vehicles"
        ],
        "weaknesses": [
            "Infantry are weaker in direct combat",
            "Fewer engineers available",
            "Less versatile structures"
        ],
        "recommended_openers": [
            "Volksgrenadiers rush for early pressure",
            "Barracks first for infantry swarm",
            "Tank Depot for fast armor"
        ],
        "counter_strategy": "Use Panzerschrecks against Allied tanks, leverage infantry numbers"
    }
}


# Difficulty doctrine adjustments
DIFFICULTY_DOCTRINES = {
    Difficulty.EASY: {
        "aggression": 0.3,
        "defense": 0.7,
        "economy_focus": 0.8,
        "risk_tolerance": 0.2,
        "description": "Defensive, economy-focused, low risk"
    },
    Difficulty.NORMAL: {
        "aggression": 0.5,
        "defense": 0.5,
        "economy_focus": 0.6,
        "risk_tolerance": 0.5,
        "description": "Balanced approach"
    },
    Difficulty.HARD: {
        "aggression": 0.7,
        "defense": 0.3,
        "economy_focus": 0.4,
        "risk_tolerance": 0.8,
        "description": "Aggressive, offensive-focused, high risk"
    },
    Difficulty.EXPERT: {
        "aggression": 0.9,
        "defense": 0.1,
        "economy_focus": 0.2,
        "risk_tolerance": 1.0,
        "description": "Highly aggressive, minimal defense, maximum risk"
    }
}


# Game phase strategies
PHASE_STRATEGIES = {
    GamePhase.EARLY: {
        "focus": "Economy and early map control",
        "priorities": [
            "Build resource structures",
            "Secure starting capture points",
            "Scout enemy positions",
            "Produce early infantry",
            "Establish forward positions"
        ],
        "avoid": [
            "Expensive tank production",
            "Over-extending without defenses",
            "Ignoring resource nodes"
        ]
    },
    GamePhase.MID: {
        "focus": "Army composition and map dominance",
        "priorities": [
            "Build tech structures (War Factory, Tank Depot)",
            "Produce mixed army (infantry + vehicles)",
            "Control majority of capture points",
            "Establish defensive lines",
            "Push enemy back"
        ],
        "avoid": [
            "Neglecting economy",
            "All-in attacks without reserves",
            "Ignoring enemy tech advancements"
        ]
    },
    GamePhase.LATE: {
        "focus": "End-game push and victory",
        "priorities": [
            "Produce heavy tanks and elite infantry",
            "Launch coordinated attacks",
            "Destroy enemy production",
            "Secure victory conditions",
            "Use abilities and special units"
        ],
        "avoid": [
            "Turtling (defensive only)",
            "Wasting resources on unnecessary units",
            "Ignoring enemy super weapons"
        ]
    }
}


# ============================================
# Prompt Engine
# ============================================

@dataclass
class PromptConfig:
    """Configuration for prompt generation."""
    faction: Faction = Faction.ALLIES
    difficulty: Difficulty = Difficulty.NORMAL
    game_phase: GamePhase = GamePhase.EARLY
    include_context: bool = True
    max_history_states: int = 5
    max_tokens: int = 2048
    temperature: float = 0.7
    
    # Custom rules
    fuel_cutoff: int = 100
    manpower_cutoff: int = 200
    munitions_cutoff: int = 50


class PromptEngine:
    """
    Generates system prompts for the Mistral AI strategist.
    
    Combines static game knowledge with dynamic game state to create
    context-aware prompts that guide the AI's decision-making.
    """
    
    def __init__(self, config: Optional[PromptConfig] = None):
        """
        Initialize the prompt engine.
        
        Args:
            config: Optional configuration
        """
        self.config = config or PromptConfig()
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"PromptEngine initialized for {self.config.faction.value} at {self.config.difficulty.value} difficulty")
    
    def generate_system_prompt(self, game_state: Optional[Dict[str, Any]] = None,
                               history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generate a complete system prompt for the strategist.
        
        Args:
            game_state: Current game state (optional, for dynamic context)
            history: Game history (optional, for context)
            
        Returns:
            Complete system prompt string
        """
        # Build game knowledge section
        game_knowledge = self._build_game_knowledge()
        
        # Build context section
        context = self._build_context(game_state, history)
        
        # Format the prompt
        prompt = BASE_SYSTEM_PROMPT.format(
            game_knowledge=game_knowledge,
            context=context
        )
        
        return prompt
    
    def _build_game_knowledge(self) -> str:
        """Build the game knowledge section of the prompt."""
        sections = []
        
        # Faction knowledge
        faction_knowledge = FACTION_KNOWLEDGE.get(self.config.faction)
        if faction_knowledge:
            sections.append("## Faction Knowledge")
            sections.append(f"You are playing as: {faction_knowledge['name']}")
            sections.append("")
            sections.append("Strengths:")
            for strength in faction_knowledge["strengths"]:
                sections.append(f"  - {strength}")
            sections.append("")
            sections.append("Weaknesses:")
            for weakness in faction_knowledge["weaknesses"]:
                sections.append(f"  - {weakness}")
            sections.append("")
            sections.append(f"Recommended Openers: {', '.join(faction_knowledge['recommended_openers'])}")
            sections.append(f"Counter Strategy: {faction_knowledge['counter_strategy']}")
            sections.append("")
        
        # Unit counter matrix
        sections.append("## Unit Counter Matrix")
        sections.append("Use this to determine which units are effective against others:")
        sections.append("")
        for unit, strengths in UNIT_STRENGTHS.items():
            strong = ", ".join(strengths.get("strong_against", []))
            weak = ", ".join(strengths.get("weak_against", []))
            if strong:
                sections.append(f"  {unit}: Strong vs [{strong}], Weak vs [{weak}]")
        sections.append("")
        
        # Resource management rules
        sections.append("## Resource Management Rules")
        sections.append(f"- Minimum fuel for tanks: {self.config.fuel_cutoff}")
        sections.append(f"- Minimum manpower for infantry: {self.config.manpower_cutoff}")
        sections.append(f"- Minimum munitions for abilities: {self.config.munitions_cutoff}")
        sections.append("- Always maintain at least 1 engineer for repairs")
        sections.append("- Keep 20% of resources in reserve for emergencies")
        sections.append("")
        
        # Building costs
        sections.append("## Building Costs and Times")
        for building, cost in BUILDING_COSTS.items():
            sections.append(f"  {building}: {cost['manpower']} MP, {cost['fuel']} Fuel, {cost['time']}s")
        sections.append("")
        
        # Unit costs
        sections.append("## Unit Costs")
        for unit, cost in UNIT_COSTS.items():
            mp = cost.get("manpower", 0)
            fuel = cost.get("fuel", 0)
            muni = cost.get("munitions", 0)
            pop = cost.get("pop", 0)
            sections.append(f"  {unit}: {mp} MP, {fuel} Fuel, {muni} Muni, {pop} Pop")
        sections.append("")
        
        # Phase strategies
        phase_strategy = PHASE_STRATEGIES.get(self.config.game_phase)
        if phase_strategy:
            sections.append(f"## {self.config.game_phase.value.upper()} Game Phase Strategy")
            sections.append(f"Focus: {phase_strategy['focus']}")
            sections.append("")
            sections.append("Priorities:")
            for priority in phase_strategy["priorities"]:
                sections.append(f"  - {priority}")
            sections.append("")
            sections.append("Avoid:")
            for avoid in phase_strategy["avoid"]:
                sections.append(f"  - {avoid}")
            sections.append("")
        
        # Difficulty doctrine
        doctrine = DIFFICULTY_DOCTRINES.get(self.config.difficulty)
        if doctrine:
            sections.append("## Difficulty Doctrine")
            sections.append(f"Current difficulty: {self.config.difficulty.value}")
            sections.append(f"Description: {doctrine['description']}")
            sections.append(f"Aggression level: {doctrine['aggression']}")
            sections.append(f"Defense level: {doctrine['defense']}")
            sections.append(f"Economy focus: {doctrine['economy_focus']}")
            sections.append(f"Risk tolerance: {doctrine['risk_tolerance']}")
            sections.append("")
        
        return "\n".join(sections)
    
    def _build_context(self, game_state: Optional[Dict[str, Any]] = None,
                       history: Optional[List[Dict[str, Any]]] = None) -> str:
        """Build the context section of the prompt."""
        if not self.config.include_context:
            return "Current game state will be provided in the user message."
        
        sections = []
        
        # Current game state
        if game_state:
            sections.append("## Current Game State")
            
            # Resources
            resources = game_state.get("resources", {})
            if resources:
                sections.append("Resources:")
                for res_type, res_data in resources.items():
                    if isinstance(res_data, dict):
                        current = res_data.get("current", 0)
                        max_res = res_data.get("max", 0)
                        income = res_data.get("income", 0)
                        sections.append(f"  {res_type}: {current}/{max_res} (+{income}/s)")
                sections.append("")
            
            # Squads
            squads = game_state.get("squads", [])
            if squads:
                sections.append(f"Squads: {len(squads)} units")
                # Group by type
                squad_types = {}
                for squad in squads:
                    s_type = squad.get("type", "unknown")
                    squad_types[s_type] = squad_types.get(s_type, 0) + 1
                for s_type, count in squad_types.items():
                    sections.append(f"  {s_type}: {count}")
                sections.append("")
            
            # Capture points
            cps = game_state.get("cps", game_state.get("capture_points", []))
            if cps:
                owned = sum(1 for cp in cps if cp.get("owner") == game_state.get("player_id", 1))
                total = len(cps)
                sections.append(f"Capture Points: {owned}/{total} controlled")
                sections.append("")
            
            # Tech tree
            tech = game_state.get("tech", game_state.get("tech_tree", {}))
            if tech:
                sections.append("Tech Tree:")
                if tech.get("tier_1"):
                    sections.append("  Tier 1: UNLOCKED")
                else:
                    sections.append("  Tier 1: LOCKED")
                if tech.get("tier_2"):
                    sections.append("  Tier 2: UNLOCKED")
                else:
                    sections.append("  Tier 2: LOCKED")
                if tech.get("tier_3"):
                    sections.append("  Tier 3: UNLOCKED")
                else:
                    sections.append("  Tier 3: LOCKED")
                sections.append("")
            
            # Population
            pop = game_state.get("pop", game_state.get("population", []))
            if pop:
                if isinstance(pop, list) and len(pop) >= 2:
                    sections.append(f"Population: {pop[0]}/{pop[1]}")
                elif isinstance(pop, dict):
                    sections.append(f"Population: {pop.get('current', 0)}/{pop.get('max', 100)}")
                sections.append("")
            
            # Game time
            game_time = game_state.get("game_time", 0)
            sections.append(f"Game Time: {game_time:.1f} seconds")
            sections.append("")
        
        # History
        if history:
            sections.append("## Recent History")
            sections.append(f"Last {len(history)} states:")
            for i, state in enumerate(history[-self.config.max_history_states:]):
                game_time = state.get("game_time", 0)
                resources = state.get("resources", {})
                mp = resources.get("manpower", {}).get("current", 0) if isinstance(resources.get("manpower"), dict) else 0
                fuel = resources.get("fuel", {}).get("current", 0) if isinstance(resources.get("fuel"), dict) else 0
                sections.append(f"  t={game_time:.1f}s: MP={mp}, Fuel={fuel}")
            sections.append("")
        
        if not game_state and not history:
            return "Current game state will be provided in the user message."
        
        return "\n".join(sections)
    
    def generate_user_prompt(self, game_state: Dict[str, Any], 
                              history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generate a user prompt with the current game state.
        
        Args:
            game_state: Current game state
            history: Optional game history
            
        Returns:
            User prompt string
        """
        # Build a compact representation of the game state
        state_str = self._format_state_for_prompt(game_state)
        
        # Add history if available
        history_str = ""
        if history:
            history_str = self._format_history_for_prompt(history)
        
        # Combine
        prompt_parts = [
            "Analyze the following game state and provide strategic intents.",
            "",
            state_str,
            history_str,
            "",
            "Provide your response as a JSON object with 'intentions' array."
        ]
        
        return "\n".join(prompt_parts)
    
    def _format_state_for_prompt(self, game_state: Dict[str, Any]) -> str:
        """Format game state for user prompt."""
        lines = []
        
        # Game info
        lines.append(f"Game Time: {game_state.get('game_time', 0):.1f}s")
        lines.append(f"Phase: {game_state.get('phase', 'unknown')}")
        lines.append(f"Faction: {game_state.get('faction', 'allies')}")
        lines.append("")
        
        # Resources
        resources = game_state.get("resources", {})
        if resources:
            lines.append("=== RESOURCES ===")
            for res_type, res_data in resources.items():
                if isinstance(res_data, dict):
                    current = res_data.get("current", 0)
                    max_res = res_data.get("max", 0)
                    income = res_data.get("income", 0)
                    lines.append(f"{res_type}: {current}/{max_res} (+{income}/s)")
            lines.append("")
        
        # Squads
        squads = game_state.get("squads", [])
        if squads:
            lines.append("=== SQUADS ===")
            for squad in squads:
                s_id = squad.get("id", 0)
                s_type = squad.get("type", "unknown")
                health = squad.get("health", 0)
                max_health = squad.get("max_health", 1)
                health_pct = (health / max_health * 100) if max_health > 0 else 0
                pos = squad.get("pos", squad.get("position", []))
                pos_str = f"({pos[0]:.0f}, {pos[1]:.0f})" if pos and len(pos) >= 2 else "unknown"
                posture = squad.get("posture", "unknown")
                in_combat = squad.get("in_combat", False)
                under_fire = squad.get("under_fire", False)
                
                status = []
                if in_combat:
                    status.append("IN_COMBAT")
                if under_fire:
                    status.append("UNDER_FIRE")
                
                status_str = f" [{', '.join(status)}]" if status else ""
                lines.append(f"  Squad {s_id} ({s_type}): {health_pct:.0f}% HP at {pos_str}, posture={posture}{status_str}")
            lines.append("")
        
        # Capture points
        cps = game_state.get("cps", game_state.get("capture_points", []))
        if cps:
            lines.append("=== CAPTURE POINTS ===")
            player_id = game_state.get("player_id", 1)
            for cp in cps:
                cp_id = cp.get("id", 0)
                owner = cp.get("owner", None)
                progress = cp.get("capture_progress", 0)
                pos = cp.get("pos", cp.get("position", []))
                pos_str = f"({pos[0]:.0f}, {pos[1]:.0f})" if pos and len(pos) >= 2 else "unknown"
                
                if owner == player_id:
                    owner_str = "OWNED"
                elif owner is None:
                    owner_str = "NEUTRAL"
                else:
                    owner_str = f"ENEMY (P{owner})"
                
                lines.append(f"  CP {cp_id} at {pos_str}: {owner_str}, progress={progress:.0%}")
            lines.append("")
        
        # Enemy units
        enemies = game_state.get("enemies", game_state.get("visible_enemies", []))
        if enemies:
            lines.append("=== VISIBLE ENEMIES ===")
            for enemy in enemies:
                e_id = enemy.get("id", 0)
                e_type = enemy.get("type", "unknown")
                health = enemy.get("health", 0)
                distance = enemy.get("distance", 0)
                pos = enemy.get("pos", enemy.get("position", []))
                pos_str = f"({pos[0]:.0f}, {pos[1]:.0f})" if pos and len(pos) >= 2 else "unknown"
                lines.append(f"  Enemy {e_id} ({e_type}): {health*100:.0f}% HP, {distance:.0f}m away at {pos_str}")
            lines.append("")
        
        # Tech tree
        tech = game_state.get("tech", game_state.get("tech_tree", {}))
        if tech:
            lines.append("=== TECH TREE ===")
            lines.append(f"  Tier 1: {'UNLOCKED' if tech.get('tier_1') else 'LOCKED'} ({tech.get('t1_progress', 0)*100:.0f}%)")
            lines.append(f"  Tier 2: {'UNLOCKED' if tech.get('tier_2') else 'LOCKED'} ({tech.get('t2_progress', 0)*100:.0f}%)")
            lines.append(f"  Tier 3: {'UNLOCKED' if tech.get('tier_3') else 'LOCKED'} ({tech.get('t3_progress', 0)*100:.0f}%)")
            abilities = tech.get("abilities", [])
            if abilities:
                lines.append(f"  Abilities: {', '.join(abilities)}")
            lines.append("")
        
        # Build queue
        queue = game_state.get("queue", game_state.get("build_queue", []))
        if queue:
            lines.append("=== BUILD QUEUE ===")
            for i, item in enumerate(queue):
                item_type = item.get("type", "unknown")
                name = item.get("name", "unknown")
                progress = item.get("progress", 0)
                time_remaining = item.get("time", 0)
                lines.append(f"  {i+1}. {name} ({item_type}): {progress*100:.0f}% ({time_remaining:.0f}s remaining)")
            lines.append("")
        
        # Population
        pop = game_state.get("pop", game_state.get("population", []))
        if pop:
            lines.append("=== POPULATION ===")
            if isinstance(pop, list) and len(pop) >= 2:
                lines.append(f"  Current: {pop[0]}/{pop[1]} ({pop[0]/pop[1]*100:.0f}%)")
            elif isinstance(pop, dict):
                current = pop.get("current", 0)
                max_pop = pop.get("max", 100)
                lines.append(f"  Current: {current}/{max_pop} ({current/max_pop*100:.0f}%)")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_history_for_prompt(self, history: List[Dict[str, Any]]) -> str:
        """Format history for user prompt."""
        lines = []
        lines.append("=== RECENT HISTORY ===")
        
        # Get last N states
        recent_states = history[-self.config.max_history_states:]
        
        for state in recent_states:
            game_time = state.get("game_time", 0)
            resources = state.get("resources", {})
            mp = resources.get("manpower", {}).get("current", 0) if isinstance(resources.get("manpower"), dict) else 0
            fuel = resources.get("fuel", {}).get("current", 0) if isinstance(resources.get("fuel"), dict) else 0
            squads = state.get("squads", [])
            cps = state.get("cps", state.get("capture_points", []))
            owned = sum(1 for cp in cps if cp.get("owner") == state.get("player_id", 1))
            total_cps = len(cps) if cps else 0
            
            lines.append(f"  t={game_time:.1f}s: MP={mp}, Fuel={fuel}, Squads={len(squads)}, CPs={owned}/{total_cps}")
        
        lines.append("")
        return "\n".join(lines)
    
    def set_faction(self, faction: Faction) -> None:
        """Set the faction for prompt generation."""
        self.config.faction = faction
        self.logger.info(f"Faction set to: {faction.value}")
    
    def set_difficulty(self, difficulty: Difficulty) -> None:
        """Set the difficulty for prompt generation."""
        self.config.difficulty = difficulty
        self.logger.info(f"Difficulty set to: {difficulty.value}")
    
    def set_game_phase(self, phase: GamePhase) -> None:
        """Set the game phase for prompt generation."""
        self.config.game_phase = phase
        self.logger.info(f"Game phase set to: {phase.value}")
    
    def set_config(self, config: PromptConfig) -> None:
        """Set the complete configuration."""
        self.config = config
        self.logger.info("Prompt configuration updated")
    
    def get_config(self) -> PromptConfig:
        """Get the current configuration."""
        return self.config


# ============================================
# Factory Functions
# ============================================

_default_engine: Optional[PromptEngine] = None


def get_prompt_engine(faction: Faction = Faction.ALLIES,
                      difficulty: Difficulty = Difficulty.NORMAL) -> PromptEngine:
    """
    Get or create the default PromptEngine singleton.
    
    Args:
        faction: Faction to use
        difficulty: Difficulty level
        
    Returns:
        PromptEngine instance
    """
    global _default_engine
    if _default_engine is None:
        config = PromptConfig(faction=faction, difficulty=difficulty)
        _default_engine = PromptEngine(config)
    return _default_engine


def reset_prompt_engine() -> None:
    """Reset the default PromptEngine singleton."""
    global _default_engine
    _default_engine = None


def create_prompt_engine(config: Optional[PromptConfig] = None) -> PromptEngine:
    """
    Create a new PromptEngine instance.
    
    Args:
        config: Optional configuration
        
    Returns:
        New PromptEngine instance
    """
    return PromptEngine(config)


if __name__ == "__main__":
    # Test the prompt engine
    print("Testing PromptEngine...")
    
    # Create engine
    engine = create_prompt_engine(PromptConfig(
        faction=Faction.ALLIES,
        difficulty=Difficulty.NORMAL,
        game_phase=GamePhase.EARLY
    ))
    
    # Generate system prompt
    system_prompt = engine.generate_system_prompt()
    print(f"\nSystem Prompt Length: {len(system_prompt)} characters")
    print("\n" + "="*80)
    print("SYSTEM PROMPT PREVIEW (first 1000 chars):")
    print("="*80)
    print(system_prompt[:1000])
    print("...")
    
    # Test with game state
    test_state = {
        "game_time": 120.5,
        "phase": "early",
        "faction": "allies",
        "player_id": 1,
        "resources": {
            "manpower": {"current": 500, "income": 10, "max": 1000},
            "fuel": {"current": 300, "income": 5, "max": 800},
            "munitions": {"current": 200, "income": 3, "max": 600}
        },
        "squads": [
            {"id": 1, "type": "riflemen", "health": 0.8, "max_health": 1.0, 
             "pos": [100, 200, 0], "posture": "defensive", "in_combat": False},
            {"id": 2, "type": "engineer", "health": 1.0, "max_health": 1.0,
             "pos": [150, 250, 0], "posture": "defensive", "in_combat": False}
        ],
        "cps": [
            {"id": 1, "pos": [500, 500, 0], "owner": 1, "capture_progress": 1.0},
            {"id": 2, "pos": [300, 400, 0], "owner": None, "capture_progress": 0.0}
        ],
        "tech": {
            "tier_1": True,
            "tier_2": False,
            "tier_3": False,
            "abilities": ["scout", "riflemen"]
        },
        "queue": [],
        "pop": [11, 100]
    }
    
    user_prompt = engine.generate_user_prompt(test_state)
    print(f"\nUser Prompt Length: {len(user_prompt)} characters")
    print("\n" + "="*80)
    print("USER PROMPT:")
    print("="*80)
    print(user_prompt)
    
    print("\nPromptEngine test completed successfully!")
