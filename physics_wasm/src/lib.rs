use std::slice;

// Global pointers to shared linear memory arrays
static mut X_PTR: *mut f32 = std::ptr::null_mut();
static mut Y_PTR: *mut f32 = std::ptr::null_mut();
static mut VX_PTR: *mut f32 = std::ptr::null_mut();
static mut VY_PTR: *mut f32 = std::ptr::null_mut();
static mut WIDTH_PTR: *mut f32 = std::ptr::null_mut();
static mut HEIGHT_PTR: *mut f32 = std::ptr::null_mut();
static mut RADIUS_PTR: *mut f32 = std::ptr::null_mut();
static mut TYPE_PTR: *mut i32 = std::ptr::null_mut();
static mut ACTIVE_PTR: *mut u8 = std::ptr::null_mut();

static mut SRC_PTR: *mut i32 = std::ptr::null_mut();
static mut TGT_PTR: *mut i32 = std::ptr::null_mut();
static mut LINK_ACTIVE_PTR: *mut u8 = std::ptr::null_mut();

static mut NUM_NODES: usize = 0;
static mut NUM_LINKS: usize = 0;

// Allocation helpers
#[no_mangle]
pub extern "C" fn alloc_nodes(num_nodes: usize) {
    unsafe {
        // Free existing arrays if allocated
        if !X_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(X_PTR, NUM_NODES)); }
        if !Y_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(Y_PTR, NUM_NODES)); }
        if !VX_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(VX_PTR, NUM_NODES)); }
        if !VY_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(VY_PTR, NUM_NODES)); }
        if !WIDTH_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(WIDTH_PTR, NUM_NODES)); }
        if !HEIGHT_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(HEIGHT_PTR, NUM_NODES)); }
        if !RADIUS_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(RADIUS_PTR, NUM_NODES)); }
        if !TYPE_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(TYPE_PTR, NUM_NODES)); }
        if !ACTIVE_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(ACTIVE_PTR, NUM_NODES)); }

        NUM_NODES = num_nodes;

        // Allocate flat boxes and convert to raw pointers
        X_PTR = Box::into_raw(vec![0.0f32; num_nodes].into_boxed_slice()) as *mut f32;
        Y_PTR = Box::into_raw(vec![0.0f32; num_nodes].into_boxed_slice()) as *mut f32;
        VX_PTR = Box::into_raw(vec![0.0f32; num_nodes].into_boxed_slice()) as *mut f32;
        VY_PTR = Box::into_raw(vec![0.0f32; num_nodes].into_boxed_slice()) as *mut f32;
        WIDTH_PTR = Box::into_raw(vec![0.0f32; num_nodes].into_boxed_slice()) as *mut f32;
        HEIGHT_PTR = Box::into_raw(vec![0.0f32; num_nodes].into_boxed_slice()) as *mut f32;
        RADIUS_PTR = Box::into_raw(vec![0.0f32; num_nodes].into_boxed_slice()) as *mut f32;
        TYPE_PTR = Box::into_raw(vec![0i32; num_nodes].into_boxed_slice()) as *mut i32;
        ACTIVE_PTR = Box::into_raw(vec![1u8; num_nodes].into_boxed_slice()) as *mut u8;
    }
}

#[no_mangle]
pub extern "C" fn alloc_links(num_links: usize) {
    unsafe {
        // Free existing arrays if allocated
        if !SRC_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(SRC_PTR, NUM_LINKS)); }
        if !TGT_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(TGT_PTR, NUM_LINKS)); }
        if !LINK_ACTIVE_PTR.is_null() { Box::from_raw(slice::from_raw_parts_mut(LINK_ACTIVE_PTR, NUM_LINKS)); }

        NUM_LINKS = num_links;

        SRC_PTR = Box::into_raw(vec![0i32; num_links].into_boxed_slice()) as *mut i32;
        TGT_PTR = Box::into_raw(vec![0i32; num_links].into_boxed_slice()) as *mut i32;
        LINK_ACTIVE_PTR = Box::into_raw(vec![1u8; num_links].into_boxed_slice()) as *mut u8;
    }
}

// Memory pointer getters
#[no_mangle] pub extern "C" fn get_x_ptr() -> *mut f32 { unsafe { X_PTR } }
#[no_mangle] pub extern "C" fn get_y_ptr() -> *mut f32 { unsafe { Y_PTR } }
#[no_mangle] pub extern "C" fn get_vx_ptr() -> *mut f32 { unsafe { VX_PTR } }
#[no_mangle] pub extern "C" fn get_vy_ptr() -> *mut f32 { unsafe { VY_PTR } }
#[no_mangle] pub extern "C" fn get_width_ptr() -> *mut f32 { unsafe { WIDTH_PTR } }
#[no_mangle] pub extern "C" fn get_height_ptr() -> *mut f32 { unsafe { HEIGHT_PTR } }
#[no_mangle] pub extern "C" fn get_radius_ptr() -> *mut f32 { unsafe { RADIUS_PTR } }
#[no_mangle] pub extern "C" fn get_type_ptr() -> *mut i32 { unsafe { TYPE_PTR } }
#[no_mangle] pub extern "C" fn get_active_ptr() -> *mut u8 { unsafe { ACTIVE_PTR } }

#[no_mangle] pub extern "C" fn get_src_ptr() -> *mut i32 { unsafe { SRC_PTR } }
#[no_mangle] pub extern "C" fn get_tgt_ptr() -> *mut i32 { unsafe { TGT_PTR } }
#[no_mangle] pub extern "C" fn get_link_active_ptr() -> *mut u8 { unsafe { LINK_ACTIVE_PTR } }

// Deterministic PRNG Seed state
static mut SEED: u32 = 123456789;
fn next_random() -> f32 {
    unsafe {
        let mut x = SEED;
        x ^= x << 13;
        x ^= x >> 17;
        x ^= x << 5;
        SEED = x;
        (x as f32) / (u32::MAX as f32) - 0.5
    }
}

// Spatial grid settings
const GRID_CELL_SIZE: f32 = 80.0;
const HASH_SIZE: usize = 2048;

#[no_mangle]
pub extern "C" fn step_simulation(layout_mode: i32, width: f32, height: f32) {
    unsafe {
        if NUM_NODES == 0 { return; }

        let x = slice::from_raw_parts_mut(X_PTR, NUM_NODES);
        let y = slice::from_raw_parts_mut(Y_PTR, NUM_NODES);
        let vx = slice::from_raw_parts_mut(VX_PTR, NUM_NODES);
        let vy = slice::from_raw_parts_mut(VY_PTR, NUM_NODES);
        let w = slice::from_raw_parts(WIDTH_PTR, NUM_NODES);
        let h = slice::from_raw_parts(HEIGHT_PTR, NUM_NODES);
        let type_id = slice::from_raw_parts(TYPE_PTR, NUM_NODES);
        let active = slice::from_raw_parts(ACTIVE_PTR, NUM_NODES);

        // 1. Swimlane Constraint Y-Forces
        if layout_mode == 1 { // 'swimlane' layout
            for i in 0..NUM_NODES {
                if active[i] == 0 || w[i] < 1.0 { continue; }
                
                let target_y = match type_id[i] {
                    1 => height * 0.23, // RULE
                    0 => height * 0.53, // FUNC
                    _ => height * 0.83, // UNRES
                };
                
                vy[i] += (target_y - y[i]) * 0.008;
            }
        }

        // 2. Repulsion Forces (Hybrid Direct O(N^2) / Spatial Hash Grid)
        if NUM_NODES <= 150 {
            // Direct O(N^2) repulsion for small repos to reduce setup overhead
            for i in 0..NUM_NODES {
                if active[i] == 0 || w[i] < 1.0 { continue; }
                for j in (i + 1)..NUM_NODES {
                    if active[j] == 0 || w[j] < 1.0 { continue; }
                    
                    let dx = x[j] - x[i];
                    let dy = y[j] - y[i];
                    let dist_sq = dx*dx + dy*dy;
                    if dist_sq > 62500.0 { continue; } // 250px cutoff
                    
                    compute_repulsion(i, j, dx, dy, dist_sq, x, y, vx, vy, w, h);
                }
            }
        } else {
            // Spatial Hash Grid repulsion for large/dense repos
            let mut bucket_heads = [-1i32; HASH_SIZE];
            let mut node_nexts = vec![-1i32; NUM_NODES];

            // Insert active nodes into grid cells
            for i in 0..NUM_NODES {
                if active[i] == 0 || w[i] < 1.0 { continue; }
                let cx = (x[i] / GRID_CELL_SIZE).floor() as i32;
                let cy = (y[i] / GRID_CELL_SIZE).floor() as i32;
                
                // Unbounded spatial hashing formula
                let cell_hash = (((cx.wrapping_mul(73856093)) ^ (cy.wrapping_mul(19349663))).wrapping_abs() as usize) % HASH_SIZE;
                
                node_nexts[i] = bucket_heads[cell_hash];
                bucket_heads[cell_hash] = i as i32;
            }

            // Compute repulsion using grid neighbors
            for i in 0..NUM_NODES {
                if active[i] == 0 || w[i] < 1.0 { continue; }
                let cx = (x[i] / GRID_CELL_SIZE).floor() as i32;
                let cy = (y[i] / GRID_CELL_SIZE).floor() as i32;

                // Loop through 3x3 cell neighborhood
                for dx_cell in -1..=1 {
                    for dy_cell in -1..=1 {
                        let ncx = cx + dx_cell;
                        let ncy = cy + dy_cell;
                        let cell_hash = (((ncx.wrapping_mul(73856093)) ^ (ncy.wrapping_mul(19349663))).wrapping_abs() as usize) % HASH_SIZE;

                        let mut j = bucket_heads[cell_hash];
                        while j != -1 {
                            let u_j = j as usize;
                            if u_j > i { // Avoid double calculations (i < j)
                                let dx = x[u_j] - x[i];
                                let dy = y[u_j] - y[i];
                                let dist_sq = dx*dx + dy*dy;
                                if dist_sq <= 62500.0 {
                                    compute_repulsion(i, u_j, dx, dy, dist_sq, x, y, vx, vy, w, h);
                                }
                            }
                            j = node_nexts[u_j];
                        }
                    }
                }
            }
        }

        // 3. Spring Forces
        if NUM_LINKS > 0 {
            let src = slice::from_raw_parts(SRC_PTR, NUM_LINKS);
            let tgt = slice::from_raw_parts(TGT_PTR, NUM_LINKS);
            let link_active = slice::from_raw_parts(LINK_ACTIVE_PTR, NUM_LINKS);

            for k in 0..NUM_LINKS {
                if link_active[k] == 0 { continue; }
                let s_idx = src[k] as usize;
                let t_idx = tgt[k] as usize;

                if s_idx >= NUM_NODES || t_idx >= NUM_NODES { continue; }
                if active[s_idx] == 0 || active[t_idx] == 0 { continue; }

                let dx = x[t_idx] - x[s_idx];
                let dy = y[t_idx] - y[s_idx];
                let mut dist = (dx*dx + dy*dy).sqrt();
                if dist < 1.0 { dist = 1.0; }

                let rest_length = 140.0;
                let k_coef = 0.07;
                let force = (dist - rest_length) * k_coef;

                let fx = (dx / dist) * force;
                let fy = (dy / dist) * force;

                vx[s_idx] += fx;
                vy[s_idx] += fy;
                vx[t_idx] -= fx;
                vy[t_idx] -= fy;
            }
        }

        // 4. Brownian Motion
        for i in 0..NUM_NODES {
            if active[i] == 0 || w[i] < 1.0 { continue; }
            vx[i] += next_random() * 0.08;
            vy[i] += next_random() * 0.08;
        }

        // 5. Center Gravity, Position Update & Velocity Capping
        let center_x = width / 2.0;
        let center_y = height / 2.0;
        let max_speed = 30.0;

        for i in 0..NUM_NODES {
            if active[i] == 0 || w[i] < 1.0 { continue; }

            // Pull to center gravity
            let dx = center_x - x[i];
            let dy = center_y - y[i];
            vx[i] += dx * 0.001;
            vy[i] += dy * 0.001;

            // Velocity capping
            let speed = (vx[i]*vx[i] + vy[i]*vy[i]).sqrt();
            if speed > max_speed {
                vx[i] = (vx[i] / speed) * max_speed;
                vy[i] = (vy[i] / speed) * max_speed;
            }

            // Apply friction/damping
            vx[i] *= 0.72;
            vy[i] *= 0.72;

            // Position update
            x[i] += vx[i];
            y[i] += vy[i];
        }
    }
}

// Helper to compute repulsion force and apply AABB overlaps between two nodes
#[inline(always)]
fn compute_repulsion(
    i: usize,
    j: usize,
    dx: f32,
    dy: f32,
    dist_sq: f32,
    x: &mut [f32],
    y: &mut [f32],
    vx: &mut [f32],
    vy: &mut [f32],
    w: &[f32],
    h: &[f32],
) {
    let mut dist = dist_sq.sqrt();
    if dist < 1.0 { dist = 1.0; }

    let strength = 950.0;
    let mut force = strength / dist_sq;
    if dist < 55.0 {
        force += (55.0 - dist) * 0.85;
    }

    let fx = (dx / dist) * force;
    let fy = (dy / dist) * force;

    vx[i] -= fx;
    vy[i] -= fy;
    vx[j] += fx;
    vy[j] += fy;

    // AABB overlap resolution (prevents nodes from visually overlapping)
    let h_width_i = w[i] / 2.0;
    let h_height_i = h[i] / 2.0;
    let h_width_j = w[j] / 2.0;
    let h_height_j = h[j] / 2.0;

    let pad_x = 14.0;
    let pad_y = 12.0;

    let min_dist_x = h_width_i + h_width_j + pad_x;
    let min_dist_y = h_height_i + h_height_j + pad_y;

    let overlap_x = min_dist_x - dx.abs();
    let overlap_y = min_dist_y - dy.abs();

    if overlap_x > 0.0 && overlap_y > 0.0 {
        if overlap_x < overlap_y {
            let sign = if dx > 0.0 { 1.0 } else { -1.0 };
            let push_force = overlap_x * 0.12 * sign;
            vx[i] -= push_force;
            vx[j] += push_force;
        } else {
            let sign = if dy > 0.0 { 1.0 } else { -1.0 };
            let push_force = overlap_y * 0.12 * sign;
            vy[i] -= push_force;
            vy[j] += push_force;
        }
    }
}
