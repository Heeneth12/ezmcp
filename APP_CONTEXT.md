import express from "express";
import cors from "cors";
import ollama from "ollama";
import { getGeminiTools, executeTool } from "./ai/toolRegistry";
import dotenv from "dotenv";
import axios from "axios";

dotenv.config();
const app = express();
app.use(express.json());

const corsOptions = {
    origin: ['https://ez-inventory.onrender.com', 'http://localhost:4200', 'http://localhost:8080'], // Add your frontend URL here
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
};
app.use(cors(corsOptions));

const port = process.env.PORT || 8085;
const devUrl = process.env.SERVER_URL + "/v1/mcp/chat";

// Helper: Fetch History & Map roles to Ollama format
async function getChatHistory(conversationId: number, token: string) {
    if (!conversationId) return [];

    try {
        const response = await axios.get(`${devUrl}/${conversationId}/messages`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        const messages = response.data.data || [];
        
        // Ollama roles: 'user', 'assistant', 'system', 'tool'
        return messages.map((msg: any) => ({
            role: msg.sender === 'user' ? 'user' : 'assistant',
            content: msg.content
        }));
    } catch (error) {
        console.warn(`Failed to load history for ${conversationId}`, error);
        return [];
    }
}

app.get("/health", (req, res) => {
    res.status(200).json({
        status: "UP",
        service: "mcp-ai-worker-local",
        model: "phi4-mini",
        timestamp: new Date().toISOString()
    });
});

app.post("/v1/ai/generate", async (req, res) => {
    try {
        const { message, conversationId } = req.body;
        const authHeader = req.headers.authorization;

        if (!authHeader) return res.status(401).json({ reply: "Unauthorized" });
        const token = authHeader.split(" ")[1];
        if (!message) return res.status(400).json({ reply: "Message required." });

        // 1. Load context
        const history = await getChatHistory(conversationId, token);
        const messages = [...history, { role: 'user', content: message }];

        // 2. Initial Model Call with Tools
        // Note: You may need to adapt getGeminiTools() to return standard JSON Schema tools for Ollama
        const response = await ollama.chat({
            model: "phi4-mini",
            messages: messages,
            tools: getGeminiTools() as any, 
        });

        let finalAiReply = "";

        // 3. Check for Tool Calls (Ollama uses tool_calls array)
        if (response.message.tool_calls && response.message.tool_calls.length > 0) {
            const toolCall = response.message.tool_calls[0];
            console.log(`🤖 Local AI invoking tool: ${toolCall.function.name}`);

            // Execute the tool logic
            const toolOutput = await executeTool(
                toolCall.function.name, 
                toolCall.function.arguments, 
                token
            );

            // Add the model's request and the tool result to the conversation
            messages.push(response.message);
            messages.push({
                role: 'tool',
                content: JSON.stringify(toolOutput)
            });

            // 4. Final generation after tool result
            const finalResponse = await ollama.chat({
                model: "phi4-mini",
                messages: messages
            });
            finalAiReply = finalResponse.message.content;
        } else {
            finalAiReply = response.message.content;
        }

        res.json({ reply: finalAiReply });

    } catch (error: any) {
        console.error("Local AI Error:", error);
        res.status(500).json({ reply: "I encountered an error with the local model service." });
    }
});

app.listen(port, () => {
    console.log(`🚀 Local MCP Worker running on port ${port} using phi4-mini`);
});

import { API_CONFIG, apiClient } from "../../config/api.config";
import { ItemModel, ItemSearchFilter } from "./item.types";

const ITEMS_BASE_URL = API_CONFIG.BASE_URL + '/v1/items';

export const ItemService = {

    /**
     * 1. GET ALL ITEMS (Paginated & Filtered)
     * Matches: POST /v1/items/all?page=0&size=10
     */
    getAll: async (page: number, size: number, filter: ItemSearchFilter, token: string) => {
        // Merge "active: true" default if you want standard behavior, or let filter override it
        const payload = {
            active: true,
            ...filter
        };
        const response = await apiClient.post(
            `${ITEMS_BASE_URL}/all?page=${page}&size=${size}`,
            payload,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    /**
     * 2. CREATE ITEM
     * Matches: POST /v1/items
     */
    create: async (item: ItemModel, token: string) => {
        const response = await apiClient.post(
            `${ITEMS_BASE_URL}`,
            item,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    /**
     * 3. GET ITEM BY ID
     * Matches: GET /v1/items/{id}
     */
    getById: async (id: number | string, token: string) => {
        const response = await apiClient.get(
            `${ITEMS_BASE_URL}/${id}`,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    /**
     * 4. UPDATE ITEM
     * Matches: POST /v1/items/{id}/update
     */
    update: async (id: number | string, item: Partial<ItemModel>, token: string) => {
        const response = await apiClient.post(
            `${ITEMS_BASE_URL}/${id}/update`,
            item,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    /**
     * 5. TOGGLE ACTIVE STATUS
     * Matches: POST /v1/items/{id}/status?active={bool}
     */
    toggleStatus: async (id: number | string, isActive: boolean, token: string) => {
        const response = await apiClient.post(
            `${ITEMS_BASE_URL}/${id}/status?active=${isActive}`,
            {}, // Empty body
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    /**
     * 6. SEARCH ITEMS (Dedicated Endpoint)
     * Matches: POST /v1/items/search
     */
    search: async (searchFilter: ItemSearchFilter, token: string) => {
        const response = await apiClient.post(
            `${ITEMS_BASE_URL}/search`,
            searchFilter,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    // --- BULK OPERATIONS ---

    /**
     * 7. GET TEMPLATE URL
     * Helper to get the template link
     */
    getTemplateUrl: () => {
        return `${ITEMS_BASE_URL}/template`;
    },

    /**
     * 8. GET BULK DOWNLOAD URL
     * Helper to get the bulk download link
     */
    getBulkDownloadUrl: () => {
        return `${ITEMS_BASE_URL}/bulk/download`;
    }
};
import { z } from "zod";
import { ItemService } from "./item.service";
import { ItemModel, ItemSearchFilter } from "./item.types";

export const itemTools = [

    //TOOL 1: Get All Items (Smart Filter)
    {
        name: "get_all_items",
        description: "Browse the full inventory catalog or items. Use this tool when the user asks to 'list', 'show', 'browse', or 'filter' items. " +
            "Useful for queries like 'Show me all items', 'List active services','List active products' or 'What brands do we have?'. " +
            "Supports filtering by Type (Goods/Services), Category, Brand, and Status.",
       // description: "Fetch a list of inventory items (PRODUCT or SERVICE). It is a items (PRODUCT/SERVICE) catalog. You can filter by Category, Brand, Type (PRODUCT/SERVICE), or Active status. If the user wants to see the next page of results, increment the 'page' parameter.",
        parameters: z.object({
            page: z.number().default(0).describe("Page number (starts at 0)"),
            size: z.number().default(10).describe("Number of items per page"),
            itemType: z.enum(['PRODUCT', 'SERVICE']).optional().describe("Filter by Item Type"),
            brand: z.string().optional().describe("Filter by Brand Name"),
            category: z.string().optional().describe("Filter by Category"),
            active: z.boolean().default(true).describe("Filter by Active status (default true)")
        }),
        execute: async (args: any, token: string) => {
            try {
                const filter: ItemSearchFilter = {
                    itemType: args.itemType ? args.itemType === "" ? null : args.itemType : null,
                    brand: args.brand,
                    category: args.category,
                    active: args.active
                };
                console.log("Fetching items with filter:", filter);
                const data = await ItemService.getAll(args.page, args.size, filter, token);
                return JSON.stringify(data);
            } catch (error: any) {
                return `Error fetching items: ${error.message}`;
            }
        }
    },

    //Search Items (Keyword Search)
    {
        name: "search_items",
        description: "Search for items using a specific keyword (matches Name or Description).",
        parameters: z.object({
            query: z.string().describe("The search keyword (e.g. 'Samsung', 'Cable')")
        }),
        execute: async (args: { query: string }, token: string) => {
            try {
                const filter: ItemSearchFilter = { searchQuery: args.query };
                // We use page 0, size 20 for search results by default
                const data = await ItemService.search(filter, token);
                return JSON.stringify(data);
            } catch (error: any) {
                return `Search failed: ${error.message}`;
            }
        }
    },

    //Add New Item
    {
        name: "add_item",
        description: "Create a new inventory item. REQUIRES: Name, Category, Unit, Purchase Price, and Selling Price.",
        parameters: z.object({
            name: z.string().describe("Item Name"),
            category: z.string().describe("Category (e.g., Electronics, Raw Material)"),
            unitOfMeasure: z.string().describe("Unit (e.g., PCS, KG, BOX)"),
            purchasePrice: z.number().describe("Buying Price (Cost)"),
            sellingPrice: z.number().describe("Selling Price (MRP/Sales)"),
            // Optional Fields
            itemType: z.enum(['PRODUCT', 'SERVICE']).default('PRODUCT'),
            brand: z.string().optional(),
            manufacturer: z.string().optional(),
            itemCode: z.string().optional().describe("Unique Item Code. If omitted, one will be generated."),
            sku: z.string().optional(),
            barcode: z.string().optional(),
            hsnSacCode: z.string().optional(),
            description: z.string().optional(),
            taxPercentage: z.number().optional(),
            discountPercentage: z.number().optional()
        }),
        execute: async (args: any, token: string) => {
            try {
                // Logic: Auto-generate code if missing (Mirroring your Angular logic)
                const generatedCode = args.itemCode || `ITM-${Math.floor(1000 + Math.random() * 9000)}`;

                const payload: ItemModel = {
                    ...args,
                    itemCode: generatedCode,
                    isActive: true // Default to true on creation
                };

                const response = await ItemService.create(payload, token);
                return `Success! Created Item '${args.name}' with Code: ${generatedCode}.`;
            } catch (error: any) {
                // Safe error handling to show message to user
                const errorMsg = error.response?.data?.message || error.message;
                return `Failed to create item. Reason: ${errorMsg}`;
            }
        }
    },

    //Edit Item
    {
        name: "edit_item",
        description: "Update details of an existing item. You MUST identify the item by its numeric ID.",
        parameters: z.object({
            id: z.number().describe("The numeric ID of the item to update"),
            // All fields are optional because we might only update one
            name: z.string().optional(),
            sellingPrice: z.number().optional(),
            purchasePrice: z.number().optional(),
            category: z.string().optional(),
            brand: z.string().optional(),
            description: z.string().optional()
        }),
        execute: async (args: any, token: string) => {
            try {
                const { id, ...updates } = args;
                await ItemService.update(id, updates, token);
                return `Successfully updated details for Item ID ${id}.`;
            } catch (error: any) {
                return `Update failed: ${error.message}`;
            }
        }
    },

    //TOOL 5: Toggle Active Status (Soft Delete)
    {
        name: "toggle_item_status",
        description: "Enable or Disable an item (Soft Delete).",
        parameters: z.object({
            id: z.number().describe("The numeric ID of the item"),
            active: z.boolean().describe("True to enable, False to disable")
        }),
        execute: async (args: { id: number, active: boolean }, token: string) => {
            try {
                await ItemService.toggleStatus(args.id, args.active, token);
                return `Item ${args.id} is now ${args.active ? 'Active' : 'Inactive'}.`;
            } catch (error: any) {
                return `Status change failed: ${error.message}`;
            }
        }
    },

    // TOOL 6: Get Bulk Template
    {
        name: "get_bulk_template",
        description: "Get the download link for the Item Import Excel Template.",
        parameters: z.object({}), // No params needed
        execute: async (_: any, token: string) => {
            try {
                const url = ItemService.getTemplateUrl();
                return `You can download the template here: ${url}`;
            } catch (error: any) {
                return `Error getting template: ${error.message}`;
            }
        }
    }
];

export interface ItemModel {
    id?: number;
    name: string;
    itemCode: string;
    sku?: string;
    barcode?: string;
    itemType: 'SERVICE' | 'PRODUCT';
    imageUrl?: string;
    category: string;
    unitOfMeasure: string;
    brand?: string;
    manufacturer?: string;
    purchasePrice: number;
    sellingPrice: number;
    mrp?: number;
    taxPercentage?: number;
    discountPercentage?: number;
    hsnSacCode?: string;
    description?: string;
    isActive: boolean;
}

export interface ItemSearchFilter {
    searchQuery?: string | null;
    active?: boolean | null;
    itemType?: 'SERVICE' | 'PRODUCT' | null;
    brand?: string | null;
    category?: string | null;
}

export interface BulkUploadResponse {
    message: string;
    downloadUrl?: string;
}
import axios from "axios";

export const API_CONFIG = {
    BASE_URL: process.env.SERVER_URL || "<http://localhost:8085>",
    TIMEOUT: 5000
};

// Create a shared Axios instance
export const apiClient = axios.create({
    baseURL: API_CONFIG.BASE_URL,
    timeout: API_CONFIG.TIMEOUT,
    headers: {
        "Content-Type": "application/json"
    }
});
import { itemTools } from "../modules/items/item.tools";

// Combine all tools here
const allTools = [
    ...itemTools,
    // ...employeeTools
];

// Format tools for Ollama (standard OpenAI-compatible JSON Schema format)
export const getGeminiTools = () => {
    return allTools.map(t => {
        const shape = (t.parameters as any).shape;
        const required = Object.keys(shape).filter(key => {
            const field = shape[key];
            const typeName = field._def?.typeName;
            return typeName !== "ZodOptional" && typeName !== "ZodDefault";
        });

        return {
            type: "function",
            function: {
                name: t.name,
                description: t.description,
                parameters: {
                    type: "object",
                    properties: getZodProperties(shape),
                    required
                }
            }
        };
    });
};

// Helper to find and execute a tool
export const executeTool = async (name: string, args: any, token: string) => {
    const tool = allTools.find(t => t.name === name);
    if (!tool) throw new Error(`Tool ${name} not found`);
    return await tool.execute(args, token);
};

// Convert Zod shape to JSON Schema properties
function getZodProperties(shape: any) {
    const properties: any = {};
    for (const key in shape) {
        const field = shape[key];
        properties[key] = zodFieldToJsonSchema(field);
    }
    return properties;
}

function zodFieldToJsonSchema(field: any): any {
    const typeName = field._def?.typeName;

    if (typeName === "ZodOptional" || typeName === "ZodDefault") {
        return zodFieldToJsonSchema(field._def.innerType);
    }
    if (typeName === "ZodNumber") return { type: "number", description: field.description };
    if (typeName === "ZodBoolean") return { type: "boolean", description: field.description };
    if (typeName === "ZodEnum") return { type: "string", enum: field._def.values, description: field.description };
    return { type: "string", description: field.description };
}
package com.ezh.Inventory.mcp.service;

import com.ezh.Inventory.mcp.dto.ChatConversationDto;
import com.ezh.Inventory.mcp.dto.ChatMessageDto;
import com.ezh.Inventory.mcp.dto.McpRequest;
import com.ezh.Inventory.mcp.entity.ChatConversation;
import com.ezh.Inventory.mcp.entity.ChatMessage;
import com.ezh.Inventory.mcp.repository.ChatConversationRepository;
import com.ezh.Inventory.mcp.repository.ChatMessageRepository;
import com.ezh.Inventory.utils.UserContextUtil;
import com.ezh.Inventory.utils.exception.CommonException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@Slf4j
@RequiredArgsConstructor
public class MCPServiceImpl implements MCPService {

    private final ChatConversationRepository chatConversationRepository;
    private final ChatMessageRepository chatMessageRepository;
    private final RestTemplate restTemplate;

    @Value("${mcp.ai.url}")
    private String mcpUrl;

    @Override
    @Transactional
    public ChatMessageDto processUserMessage(String userMessage, Long conversationId, String authToken) {

        // 1. Get Context
        Long tenantId = UserContextUtil.getTenantIdOrThrow();
        Long userId = UserContextUtil.getUserId();

        // 2. Retrieve or Create Conversation
        ChatConversation conversation;
        if (conversationId != null && conversationId > 0) {
            conversation = chatConversationRepository.findById(conversationId)
                    .orElseThrow(() -> new CommonException("Conversation not found", HttpStatus.NOT_FOUND));
        } else {
            // Auto-create if ID is missing (First message)
            conversation = createConversationInternal(userMessage, tenantId, userId);
        }

        // 3. Save User Message to DB
        ChatMessage userMsgEntity = ChatMessage.builder()
                .conversation(conversation)
                .sender("user")
                .content(userMessage)
                .timestamp(new Date())
                .build();
        chatMessageRepository.save(userMsgEntity);

        // Update conversation "last updated" time (for sorting history)
        conversation.setUpdatedAt(new Date());
        chatConversationRepository.save(conversation);

        // 4. Prepare Data for Node.js
        McpRequest mcpRequest = McpRequest.builder()
                .message(userMessage)
                .conversationId(conversation.getId())
                .tenantId(tenantId)
                .userId(userId)
                .build();

        // 5. Call Node.js MCP Server
        String aiResponseText = callMCPServer(mcpRequest, authToken);

        // 6. Save AI Response to DB
        ChatMessage aiMsgEntity = ChatMessage.builder()
                .conversation(conversation)
                .sender("ai")
                .content(aiResponseText)
                .timestamp(new Date())
                .build();
        chatMessageRepository.save(aiMsgEntity);

        // 7. Return DTO (Frontend needs the new conversationId if it was just created)
        return ChatMessageDto.builder()
                .id(aiMsgEntity.getId())
                .conversationId(conversation.getId())
                .content(aiResponseText)
                .sender("ai")
                .timestamp(aiMsgEntity.getTimestamp())
                .build();
    }

    @Override
    @Transactional(readOnly = true)
    public List<ChatConversationDto> getUserConversations() {
        Long tenantId = UserContextUtil.getTenantIdOrThrow();
        List<ChatConversation> conversations = chatConversationRepository.findByTenantIdOrderByUpdatedAtDesc(tenantId);
        return conversations.stream().map(this::buildConversationDto).collect(Collectors.toList());
    }

    @Override
    @Transactional(readOnly = true)
    public List<ChatMessageDto> getConversationMessages(Long conversationId) {
        List<ChatMessage> messages = chatMessageRepository.findByConversationIdOrderByTimestampAsc(conversationId);
        return messages.stream().map(this::buildMessageDto).collect(Collectors.toList());
    }


    private String callMCPServer(McpRequest requestPayload, String token) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            // Forward the Bearer token so Node.js can make authorized callbacks if needed
            if (token != null && !token.startsWith("Bearer ")) {
                token = "Bearer " + token;
            }
            headers.set("Authorization", token);

            HttpEntity<McpRequest> request = new HttpEntity<>(requestPayload, headers);

            // Call Node Server
            ResponseEntity<Map> response = restTemplate.postForEntity(mcpUrl, request, Map.class);

            if (response.getBody() != null && response.getBody().containsKey("reply")) {
                return (String) response.getBody().get("reply");
            }
            return "No response received from AI.";

        } catch (Exception e) {
            log.error("Error calling AI Node Server: {}", e.getMessage());
            return "I'm having trouble connecting to my brain right now. Please try again.";
        }
    }

    private ChatConversation createConversationInternal(String firstMessage, Long tenantId, Long userId) {
        String title = firstMessage.length() > 30 ? firstMessage.substring(0, 30) + "..." : firstMessage;
        ChatConversation conversation = ChatConversation.builder()
                .tenantId(tenantId)
                .title(title)
                .appKey("EZH_INV_001") // Or pass dynamically if needed
                .createdBy(String.valueOf(userId))
                .createdAt(new Date())
                .updatedAt(new Date())
                .build();

        return chatConversationRepository.save(conversation);
    }

    private ChatConversationDto buildConversationDto(ChatConversation entity) {
        if (entity == null) return null;
        return ChatConversationDto.builder()
                .id(entity.getId())
                .tenantId(entity.getTenantId())
                .title(entity.getTitle())
                .createdAt(entity.getCreatedAt())
                .build();
    }

    private ChatMessageDto buildMessageDto(ChatMessage entity) {
        if (entity == null) return null;
        return ChatMessageDto.builder()
                .id(entity.getId())
                .conversationId(entity.getConversation().getId())
                .sender(entity.getSender())
                .content(entity.getContent())
                .timestamp(entity.getTimestamp())
                .build();
    }
}

## - > python -m uvicorn main:app --host 0.0.0.0 --port 8086 --reload
